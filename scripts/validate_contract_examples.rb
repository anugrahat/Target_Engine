#!/usr/bin/env ruby
# frozen_string_literal: true

require "json"
require "pathname"
require_relative "lib/simple_schema_validator"

ROOT = Pathname(__dir__).parent
SCHEMAS_DIR = ROOT.join("data_contracts/schemas")
EXAMPLES_DIR = ROOT.join("data_contracts/examples")

example_paths = Dir[EXAMPLES_DIR.join("*.json").to_s].sort

if example_paths.empty?
  warn "No example contract files found in #{EXAMPLES_DIR}"
  exit 1
end

all_errors = []

example_paths.each do |example_path|
  schema_prefix = File.basename(example_path).split(".", 2).first
  schema_path = SCHEMAS_DIR.join("#{schema_prefix}.schema.json")

  unless schema_path.exist?
    all_errors << "#{example_path}: no schema found at #{schema_path}"
    next
  end

  begin
    schema = JSON.parse(File.read(schema_path))
    data = JSON.parse(File.read(example_path))
  rescue JSON::ParserError => e
    all_errors << "#{example_path}: JSON parse error: #{e.message}"
    next
  end

  errors = []
  SimpleSchemaValidator.validate_node(data, schema, File.basename(example_path), errors)
  if errors.empty?
    puts "PASS #{example_path}"
  else
    all_errors.concat(errors.map { |error| "#{example_path}: #{error}" })
  end
end

unless all_errors.empty?
  warn "\nContract example validation failed:"
  all_errors.each { |error| warn "- #{error}" }
  exit 1
end

puts "\nValidated #{example_paths.length} contract example(s)."
