#!/usr/bin/env ruby
# frozen_string_literal: true

require "json"
require "pathname"
require "psych"
require_relative "lib/simple_schema_validator"

ROOT = Pathname(__dir__).parent
SCHEMA_PATH = ROOT.join("data_contracts/schemas/benchmark_subset.schema.json")
SUBSETS_DIR = ROOT.join("configs/subsets")

schema = JSON.parse(SCHEMA_PATH.read)
subset_paths = Dir[SUBSETS_DIR.join("*.yaml").to_s].sort

if subset_paths.empty?
  warn "No subset configs found in #{SUBSETS_DIR}"
  exit 1
end

all_errors = []

subset_paths.each do |subset_path|
  begin
    data = Psych.safe_load(File.read(subset_path), aliases: false)
  rescue Psych::Exception => e
    all_errors << "#{subset_path}: YAML parse error: #{e.message}"
    next
  end

  unless data.is_a?(Hash)
    all_errors << "#{subset_path}: top-level document must be an object"
    next
  end

  errors = []
  SimpleSchemaValidator.validate_node(data, schema, File.basename(subset_path), errors)
  if errors.empty?
    puts "PASS #{subset_path}"
  else
    all_errors.concat(errors.map { |error| "#{subset_path}: #{error}" })
  end
end

unless all_errors.empty?
  warn "\nSubset config validation failed:"
  all_errors.each { |error| warn "- #{error}" }
  exit 1
end

puts "\nValidated #{subset_paths.length} subset config(s)."
