#!/usr/bin/env ruby
# frozen_string_literal: true

require "json"
require "pathname"
require "psych"
require_relative "lib/simple_schema_validator"

ROOT = Pathname(__dir__).parent
SCHEMA_PATH = ROOT.join("data_contracts/schemas/benchmark_pack.schema.json")
PACKS_DIR = ROOT.join("configs/indications")

schema = JSON.parse(SCHEMA_PATH.read)
pack_paths = Dir[PACKS_DIR.join("*.yaml").to_s].sort

if pack_paths.empty?
  warn "No benchmark packs found in #{PACKS_DIR}"
  exit 1
end

all_errors = []

pack_paths.each do |pack_path|
  begin
    data = Psych.safe_load(File.read(pack_path), aliases: false)
  rescue Psych::Exception => e
    all_errors << "#{pack_path}: YAML parse error: #{e.message}"
    next
  end

  unless data.is_a?(Hash)
    all_errors << "#{pack_path}: top-level document must be an object"
    next
  end

  errors = []
  SimpleSchemaValidator.validate_node(data, schema, File.basename(pack_path), errors)
  if errors.empty?
    puts "PASS #{pack_path}"
  else
    all_errors.concat(errors.map { |error| "#{pack_path}: #{error}" })
  end
end

unless all_errors.empty?
  warn "\nBenchmark pack validation failed:"
  all_errors.each { |error| warn "- #{error}" }
  exit 1
end

puts "\nValidated #{pack_paths.length} benchmark pack(s)."
