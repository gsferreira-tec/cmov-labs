#!/usr/bin/env python3
import sys
import subprocess
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 flowmon-wrapper.py <path/to/xml_folder> <output_log.txt>")
        sys.exit(1)

    xml_folder= Path(sys.argv[1])
    output_txt = Path(sys.argv[2])
    parser_script= Path("/home/mobile/Share/flowmon-parse-results.py")

    if not xml_folder.is_dir():
        print(f"Error: {xml_folder} is not a directory")
        sts.exit(1)

    if not parser_script.is_file():
        print(f"Error: {parser_script} does not exits")
        sys.exit(1)

    xml_files = sorted(xml_folder.glob("*.xml"))

    if not xml_files:
        print(f"No XML files found in {xml_folder}")
        sys.exit(1)

    with output_txt.open("w", encoding="utf-8") as out:
        for xml_file in xml_files:
            header = f"********** {xml_file.name} **********"
            print(header)
            out.write(header + "\n")

            result = subprocess.run(["python3", str(parser_script), str(xml_file)],
                                    capture_output=True,
                                    text=True
                                )

            if result.returncode != 0:
                print(f"Error processing {xml_file.name}")
                print(err)
                print(result.stderr.strip())
                out.write(err+"\n")
                out.write(result.stderr.strip() + "\n")
                continue

            print(result.stdout.strip())
            out.write(result.stdout.strip() + "\n")

if __name__ == "__main__":
    main()
