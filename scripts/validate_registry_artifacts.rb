#!/usr/bin/env ruby
# frozen_string_literal: true

require "json"
require "pathname"
require_relative "lib/simple_schema_validator"

ROOT = Pathname(__dir__).parent
SCHEMAS_DIR = ROOT.join("data_contracts/schemas")
REGISTRIES_DIR = ROOT.join("data_contracts/registries")

artifact_paths = Dir[REGISTRIES_DIR.join("**/*.json").to_s].sort

if artifact_paths.empty?
  warn "No registry artifacts found in #{REGISTRIES_DIR}"
  exit 1
end

all_errors = []

artifact_paths.each do |artifact_path|
  schema_prefix = File.basename(artifact_path).split(".", 2).first
  schema_path = SCHEMAS_DIR.join("#{schema_prefix}.schema.json")

  unless schema_path.exist?
    all_errors << "#{artifact_path}: no schema found at #{schema_path}"
    next
  end

  begin
    schema = JSON.parse(File.read(schema_path))
    data = JSON.parse(File.read(artifact_path))
  rescue JSON::ParserError => e
    all_errors << "#{artifact_path}: JSON parse error: #{e.message}"
    next
  end

  errors = []
  SimpleSchemaValidator.validate_node(data, schema, File.basename(artifact_path), errors)
  if errors.empty?
    puts "PASS #{artifact_path}"
  else
    all_errors.concat(errors.map { |error| "#{artifact_path}: #{error}" })
  end
end

unless all_errors.empty?
  warn "\nRegistry artifact validation failed:"
  all_errors.each { |error| warn "- #{error}" }
  exit 1
end

puts "\nValidated #{artifact_paths.length} registry artifact(s)."
