import codecs

def extract_deleted():
    deleted_lines = []
    with codecs.open('diff.txt', 'r', encoding='utf-16') as f:
        in_deletion_block = False
        for line in f:
            if line.startswith('@@ '):
                # Start tracking
                pass
            if line.startswith('-') and not line.startswith('---'):
                # Line was deleted
                deleted_lines.append(line[1:]) # remove the leading '-'
            elif line.startswith('+') and not line.startswith('+++'):
                pass
            elif line.startswith(' '):
                pass
    with codecs.open('restored_endpoints.py', 'w', encoding='utf-8') as out:
        out.writelines(deleted_lines)
    print("Done")

extract_deleted()
