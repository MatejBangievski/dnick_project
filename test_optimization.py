#!/usr/bin/env python3
"""
Test script to verify image file optimization is working correctly.
Run this after starting the Django server and performing some operations.
"""

import os
import sys
from pathlib import Path

def check_temp_directory():
    """Check the temp_edited_images directory and count files."""

    # Adjust this path if your project structure is different
    project_root = Path(__file__).parent
    media_dir = project_root / "editorproject" / "media" / "temp_edited_images"

    if not media_dir.exists():
        print(f"❌ Temp directory does not exist: {media_dir}")
        return

    files = list(media_dir.glob("*"))
    image_files = [f for f in files if f.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif']]

    print("=" * 60)
    print("🔍 IMAGE FILE OPTIMIZATION CHECK")
    print("=" * 60)
    print(f"\n📁 Directory: {media_dir}\n")

    if not image_files:
        print("✅ No temporary files found (clean state)")
        print("   This is expected if no active editing session exists.\n")
        return

    print(f"📊 Total image files: {len(image_files)}\n")

    # Group files by session ID (prefix pattern)
    sessions = {}
    for file in image_files:
        name = file.stem  # filename without extension

        # Check for optimized naming pattern
        if name.startswith(('original_', 'working_', 'preview_')):
            parts = name.split('_', 1)
            if len(parts) == 2:
                file_type, session_id = parts
                if session_id not in sessions:
                    sessions[session_id] = {}
                sessions[session_id][file_type] = file
        else:
            # Old UUID-based files (if any remain)
            if 'old_format' not in sessions:
                sessions['old_format'] = {}
            sessions['old_format'][name] = file

    # Analyze results
    print("📋 File Analysis:\n")

    for session_id, files_dict in sessions.items():
        if session_id == 'old_format':
            print(f"⚠️  Old format files (SHOULD NOT EXIST after optimization):")
            for name, file in files_dict.items():
                print(f"   - {file.name}")
        else:
            print(f"✅ Session: {session_id}")
            for file_type in ['original', 'working', 'preview']:
                if file_type in files_dict:
                    file = files_dict[file_type]
                    size_kb = file.stat().st_size / 1024
                    print(f"   - {file_type:8s}: {file.name} ({size_kb:.1f} KB)")
                else:
                    print(f"   - {file_type:8s}: ❌ MISSING")
            print()

    # Final verdict
    print("=" * 60)
    if len(sessions) == 1 and 'old_format' not in sessions:
        session_files = list(sessions.values())[0]
        if len(session_files) == 3 and all(ft in session_files for ft in ['original', 'working', 'preview']):
            print("✅ OPTIMIZATION SUCCESS!")
            print("   Exactly 3 files with correct naming pattern.")
        else:
            print("⚠️  Partial optimization: 1 session but missing files")
    elif len(sessions) == 0:
        print("✅ CLEAN STATE - No active sessions")
    elif 'old_format' in sessions:
        print("❌ OPTIMIZATION ISSUE DETECTED!")
        print("   Old UUID-based files found. These should not exist.")
        print("   Please check if the code changes were applied correctly.")
    elif len(sessions) > 1:
        print("⚠️  Multiple sessions detected")
        print("   This is normal if you uploaded multiple images.")
        print(f"   Total sessions: {len(sessions)}")
        if len(image_files) <= len(sessions) * 3:
            print("   ✅ File count is optimal (3 files per session)")
        else:
            print("   ⚠️  More files than expected")

    print("=" * 60)

def main():
    print("\n" + "=" * 60)
    print("Image File Optimization Verification Script")
    print("=" * 60 + "\n")

    check_temp_directory()

    print("\n💡 TESTING INSTRUCTIONS:")
    print("-" * 60)
    print("1. Start your Django server")
    print("2. Upload an image in the editor")
    print("3. Apply some edits")
    print("4. Click 'Reset Image' multiple times")
    print("5. Run this script again")
    print("\n   Expected result: Only 3 files in temp directory")
    print("   (original_XXX.ext, working_XXX.ext, preview_XXX.ext)")
    print("\n6. Upload a different image")
    print("7. Run this script again")
    print("\n   Expected result: Old 3 files deleted, new 3 files created")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()

