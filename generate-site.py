#!/usr/bin/env python3
"""
Red Flags Profits - Website Generation Script
Fixed to work with AdaptedLightweightGenerator
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from generator import AdaptedLightweightGenerator


def main():
    """Generate the static website"""
    print("🚀 Starting Red Flags Profits website generation...")

    generator = AdaptedLightweightGenerator()
    success = generator.generate_site()

    if success:
        print("\n🎉 Website generation completed successfully!")
        print("📖 To serve locally: cd docs && python -m http.server 8000")
        return 0
    else:
        print("\n❌ Website generation failed!")
        return 1


if __name__ == "__main__":
    exit(main())
