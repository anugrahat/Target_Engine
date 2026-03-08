#!/usr/bin/env ruby
# frozen_string_literal: true

require "json"
require "pathname"
require "psych"

ROOT = Pathname(__dir__).parent
SCHEMA_PATH = ROOT.join("data_contracts/schemas/benchmark_pack.schema.json")
PACKS_DIR = ROOT.join("configs/indications")

def matches_type?(value, type_name)
  case type_name
  when "string"
    value.is_a?(String)
  when "object"
    value.is_a?(Hash)
  when "array"
    value.is_a?(Array)
  when "integer"
    value.is_a?(Integer)
  when "null"
    value.nil?
  else
    false
  end
end

def validate_node(value, schema, path, errors)
  if schema.key?("type")
    allowed_types = schema["type"].is_a?(Array) ? schema["type"] : [schema["type"]]
    unless allowed_types.any? { |type_name| matches_type?(value, type_name) }
      errors << "#{path}: expected #{allowed_types.join(' or ')}, got #{value.class}"
      return
    end
  end

  if schema.key?("enum") && !schema["enum"].include?(value)
    errors << "#{path}: expected one of #{schema['enum'].inspect}, got #{value.inspect}"
  end

  return if value.nil?

  case value
  when Hash
    required = schema.fetch("required", [])
    required.each do |key|
      errors << "#{path}: missing required key #{key.inspect}" unless value.key?(key)
    end

    properties = schema.fetch("properties", {})
    if schema["additionalProperties"] == false
      unknown_keys = value.keys - properties.keys
      unknown_keys.each do |key|
        errors << "#{path}: unexpected key #{key.inspect}"
      end
    end

    properties.each do |key, child_schema|
      next unless value.key?(key)
      validate_node(value[key], child_schema, "#{path}.#{key}", errors)
    end
  when Array
    min_items = schema["minItems"]
    if min_items && value.length < min_items
      errors << "#{path}: expected at least #{min_items} items, got #{value.length}"
    end

    item_schema = schema["items"]
    return unless item_schema

    value.each_with_index do |item, index|
      validate_node(item, item_schema, "#{path}[#{index}]", errors)
    end
  end
end

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
  validate_node(data, schema, File.basename(pack_path), errors)
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
