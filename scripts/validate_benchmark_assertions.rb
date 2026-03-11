#!/usr/bin/env ruby
# frozen_string_literal: true

require "json"
require "pathname"
require_relative "lib/simple_schema_validator"

ROOT = Pathname(__dir__).parent
SCHEMA_PATH = ROOT.join("data_contracts/schemas/benchmark_target_assertion.schema.json")
ASSERTIONS_DIR = ROOT.join("data_contracts/assertions")

assertion_paths = Dir[ASSERTIONS_DIR.join("*.json").to_s].sort

if assertion_paths.empty?
  warn "No benchmark assertion files found in #{ASSERTIONS_DIR}"
  exit 1
end

schema = JSON.parse(File.read(SCHEMA_PATH))
all_errors = []

assertion_paths.each do |assertion_path|
  begin
    data = JSON.parse(File.read(assertion_path))
  rescue JSON::ParserError => e
    all_errors << "#{assertion_path}: JSON parse error: #{e.message}"
    next
  end

  errors = []
  SimpleSchemaValidator.validate_node(data, schema, File.basename(assertion_path), errors)
  if errors.empty?
    puts "PASS #{assertion_path}"
  else
    all_errors.concat(errors.map { |error| "#{assertion_path}: #{error}" })
  end
end

unless all_errors.empty?
  warn "\nBenchmark assertion validation failed:"
  all_errors.each { |error| warn "- #{error}" }
  exit 1
end

puts "\nValidated #{assertion_paths.length} benchmark assertion file(s)."
