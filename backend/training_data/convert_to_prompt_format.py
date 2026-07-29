"""
Convert conversations format to prompt/response format for LoRA training.

Transforms:
  {"conversations": [{"from": "system", ...}, {"from": "user", ...}, {"from": "assistant", ...}]}
  
Into:
  {"prompt": "<system prompt>\n\n<user prompt>", "response": "<assistant response>"}
"""
import json
import os


def convert_conversations_to_prompt_response(conversations):
    """Convert conversations format to prompt/response format."""
    system_msg = ""
    user_msg = ""
    assistant_msg = ""
    
    for msg in conversations:
        if msg["from"] == "system":
            system_msg = msg["value"]
        elif msg["from"] == "user":
            user_msg = msg["value"]
        elif msg["from"] == "assistant":
            assistant_msg = msg["value"]
    
    # Combine system and user messages as prompt
    if system_msg:
        prompt = f"{system_msg}\n\n{user_msg}"
    else:
        prompt = user_msg
    
    return {
        "prompt": prompt,
        "response": assistant_msg
    }


def convert_file(input_file, output_file):
    """Convert entire JSONL file from conversations to prompt/response format."""
    converted_count = 0
    skipped_count = 0
    
    print(f"🔄 Converting {input_file} → {output_file}")
    
    with open(input_file, 'r', encoding='utf-8') as f_in, \
         open(output_file, 'w', encoding='utf-8') as f_out:
        
        for line_num, line in enumerate(f_in, 1):
            line = line.strip()
            if not line:
                continue
            
            try:
                data = json.loads(line)
                
                # Check if it has conversations format
                if "conversations" in data:
                    converted = convert_conversations_to_prompt_response(data["conversations"])
                    
                    # Validate conversion
                    if converted["prompt"] and converted["response"]:
                        f_out.write(json.dumps(converted, ensure_ascii=False) + '\n')
                        converted_count += 1
                    else:
                        print(f"⚠️  Line {line_num}: Empty prompt or response after conversion")
                        skipped_count += 1
                
                # Already in prompt/response format
                elif "prompt" in data and "response" in data:
                    f_out.write(line + '\n')
                    converted_count += 1
                
                else:
                    print(f"⚠️  Line {line_num}: Unknown format (no 'conversations' or 'prompt/response')")
                    skipped_count += 1
                
            except json.JSONDecodeError as e:
                print(f"❌ Line {line_num}: JSON parse error - {e}")
                skipped_count += 1
            except Exception as e:
                print(f"❌ Line {line_num}: Unexpected error - {e}")
                skipped_count += 1
            
            if (line_num % 500) == 0:
                print(f"   Processed {line_num} lines... ({converted_count} converted, {skipped_count} skipped)")
    
    print(f"\n✅ Conversion complete!")
    print(f"   📊 Total converted: {converted_count}")
    print(f"   ⚠️  Total skipped: {skipped_count}")
    print(f"   💾 Output file: {output_file}")
    
    if os.path.exists(output_file):
        size_mb = os.path.getsize(output_file) / 1024 / 1024
        print(f"   📁 File size: {size_mb:.2f} MB")
    
    return converted_count, skipped_count


def main():
    """Convert training data files."""
    input_file = "study_planner_train.jsonl"
    output_file = "study_planner_train_prompt_format.jsonl"
    
    if not os.path.exists(input_file):
        print(f"❌ Input file not found: {input_file}")
        return
    
    converted, skipped = convert_file(input_file, output_file)
    
    # Create validation split (10%)
    if converted > 0:
        print(f"\n🔀 Creating validation split (10%)...")
        
        with open(output_file, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
        
        # Shuffle
        import random
        random.seed(42)
        random.shuffle(all_lines)
        
        # Split
        val_size = int(len(all_lines) * 0.1)
        train_lines = all_lines[val_size:]
        val_lines = all_lines[:val_size]
        
        # Write train split
        train_output = "study_planner_train_split.jsonl"
        with open(train_output, 'w', encoding='utf-8') as f:
            f.writelines(train_lines)
        
        # Write validation split
        val_output = "study_planner_val.jsonl"
        with open(val_output, 'w', encoding='utf-8') as f:
            f.writelines(val_lines)
        
        print(f"   ✅ Train: {len(train_lines)} examples → {train_output}")
        print(f"   ✅ Val: {len(val_lines)} examples → {val_output}")


if __name__ == "__main__":
    main()
