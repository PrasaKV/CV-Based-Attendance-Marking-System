import re


class RosterParser:
    """Extracts student index/name pairs from a simple pseudo-XML roster file."""

    INDEX_PATTERN = re.compile(r"<index[^>]*>([^<]+)</index>")
    NAME_PATTERN = re.compile(r"<name>([^<]+)</name>")

    @classmethod
    def load(cls, path):
        try:
            with open(path, "r") as f:
                content = f.read()
        except OSError as e:
            print(f"Could not read roster file: {e}")
            return []

        indices = cls.INDEX_PATTERN.findall(content)
        names = cls.NAME_PATTERN.findall(content)

        return [
            {"index": idx.strip(), "name": name.strip()}
            for idx, name in zip(indices, names)
        ]
