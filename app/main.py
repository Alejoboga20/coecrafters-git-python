import sys
import os
import zlib


def read_file(file_path):
    with open(file_path, "rb") as file:
        return file.read()


def extract_file_content(compressed_data: bytes) -> str:
    file_decompressed = zlib.decompress(compressed_data).decode("utf-8")
    _, file_content = file_decompressed.split("\x00", 1)
    cleaned_file_content = file_content.rstrip()

    return cleaned_file_content


def main():
    print("Logs from your program will appear here!", file=sys.stderr)

    args = sys.argv
    command = args[1]

    if command == "init":
        os.mkdir(".git")
        os.mkdir(".git/objects")
        os.mkdir(".git/refs")
        with open(".git/HEAD", "w") as f:
            f.write("ref: refs/heads/main\n")
        print("Initialized git directory")

    if command == "cat-file":
        if len(args) < 3:
            raise RuntimeError(f"Not enough arguments for {command} command")

        flag = args[2]
        obj = args[3]

        if flag == "-p":
            SHA1_prefix = obj[:2]
            SHA1_suffix = obj[2:]
            file_path = f".git/objects/{SHA1_prefix}/{SHA1_suffix}"

            compressed_data = read_file(file_path)
            decompressed_data = extract_file_content(compressed_data)

            print(decompressed_data, end="")

    else:
        raise RuntimeError(f"Unknown command #{command}")


if __name__ == "__main__":
    main()
