import sys
import os
import zlib
import hashlib

valid_commands = ["init", "cat-file", "hash-object", "ls-tree", "write-tree"]

tree_modes = {
    "blob": "100644",
    "directory": "40000",
}


def read_working_directory():
    tree_entries: list[str] = []
    working_directory = os.getcwd()

    for root, directories, files in os.walk(working_directory):
        if ".git" in directories:
            directories.remove(".git")

        for file in files:
            file_path = os.path.join(root, file)
            encoded_file = read_file_as_str(file_path)
            _, blob_content = create_blob_object(encoded_file)
            git_sha1 = create_git_sha1(blob_content)
            tree_entry = f"{tree_modes['blob']} {file}\x00{git_sha1}"
            tree_entries.append(tree_entry)

        print(tree_entries)

    return


def extract_tree_content(compressed_data: bytes):
    tree_entries: list[str] = []
    names_only: str = ""
    decompressed_data = zlib.decompress(compressed_data)
    header, body = decompressed_data.split(b"\x00", 1)

    object_type, _ = header.decode().split(" ")
    if object_type != "tree":
        raise ValueError(f"Expected a tree object, but got: {object_type}")

    while body:
        mode_end = body.find(b" ")
        if mode_end == -1:
            break

        name_end = body.find(b"\x00", mode_end + 1)
        if name_end == -1:
            break

        file_name = body[mode_end + 1:name_end].decode()
        tree_entries.append(file_name)

        body = body[name_end + 1 + 20:]

    for entry in tree_entries:
        names_only += f"{entry}\n"

    return names_only


def read_file_as_bytes(file_path: str) -> bytes:
    with open(file_path, "rb") as file:
        return file.read()


def read_file_as_str(file_path: str) -> str:
    with open(file_path, "r") as file:
        return file.read()


def extract_file_content(compressed_data: bytes) -> str:
    file_decompressed = zlib.decompress(compressed_data).decode("utf-8")
    _, file_content = file_decompressed.split("\x00", 1)
    cleaned_file_content = file_content.rstrip()

    return cleaned_file_content


def create_blob_object(file_content: str) -> tuple[bytes, str]:
    header = f"blob {len(file_content)}\x00"
    blob_content = header + file_content
    blob_object = zlib.compress(header.encode() + file_content.encode())

    return blob_object, blob_content


def create_git_sha1(blob_content: str) -> str:
    if isinstance(blob_content, str):
        blob_to_hash = blob_content.encode()

    hash = hashlib.sha1(blob_to_hash).hexdigest()

    return hash


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

            compressed_data = read_file_as_bytes(file_path)
            decompressed_data = extract_file_content(compressed_data)

            print(decompressed_data, end="")

    if command == "hash-object":
        if len(args) < 3:
            raise RuntimeError(f"Not enough arguments for {command} command")

        encoded_file = read_file_as_str(f"{args[3]}")
        blob_object, blob_content = create_blob_object(encoded_file)
        git_sha1 = create_git_sha1(blob_content)

        SHA1_prefix = git_sha1[:2]
        SHA1_suffix = git_sha1[2:]
        file_path = f".git/objects/{SHA1_prefix}/{SHA1_suffix}"

        if not os.path.exists(file_path):
            os.makedirs(f".git/objects/{SHA1_prefix}")
            with open(file_path, "wb") as f:
                f.write(blob_object)

        print(git_sha1)

    if command == "ls-tree":
        if len(args) < 3:
            raise RuntimeError(f"Not enough arguments for {command} command")

        flag = args[2]
        git_sha1 = args[3]
        SHA1_prefix = git_sha1[:2]
        SHA1_suffix = git_sha1[2:]
        file_path = f".git/objects/{SHA1_prefix}/{SHA1_suffix}"

        if not os.path.exists(file_path):
            raise RuntimeError(f"Object {git_sha1} not found")

        compressed_data = read_file_as_bytes(file_path)
        tree_content = extract_tree_content(compressed_data)

        print(tree_content, end="")

    if command == "write-tree":
        read_working_directory()

    if command not in valid_commands:
        raise RuntimeError(f"Unknown command #{command}")


if __name__ == "__main__":
    main()
