import numpy as np
from rapidfuzz.string_metric import levenshtein_editops
from rapidfuzz.fuzz import ratio
from pathlib import Path

def seq_align(s1, s2):
    """Align general sequences."""
    seq1, seq2 = "", ""
    ops = levenshtein_editops(s1, s2)
    last_op = None
    if ops == []:
        yield s1, s2
        return

    def report(op, seq1, seq2):
        if op[0] == "insert": seq1 = None
        elif op[0] == 'delete': seq2 = None
        return seq1, seq2

    for op in ops:
        if not last_op:
            yield s1[:op[1]], s2[:op[2]]
            last_op = op
        if op[0] == "insert":
            if last_op[1] != op[1]:
                yield report(last_op, seq1, seq2)
                yield s1[last_op[1] + 1:op[1]], s2[last_op[2] + 1:op[2]]
                seq1, seq2 = "", ""
            seq2 += s2[op[2]]
            op = (op[0],op[1],(op[2]+1))
        elif op[0] == "delete":
            if last_op[2] != op[2]:
                yield report(last_op, seq1, seq2)
                yield s1[last_op[1]:op[1]], s2[last_op[2]:op[2]]
                seq1, seq2 = "", ""
            seq1 += s1[op[1]]
            op = (op[0],(op[1]+1),op[2])
        elif op[0] == "replace":
            if not (last_op[1]+1 >= op[1] or last_op[2] >= op[2]):
                yield report(last_op, seq1, seq2)
                yield s1[last_op[1]:op[1]], s2[last_op[2]:op[2]]
                seq1, seq2 = "", ""
            seq1 += s1[op[1]]
            seq2 += s2[op[2]]
            op = (op[0], (op[1]+1), (op[2] + 1))
        last_op = op
    yield report(last_op, seq1, seq2)
    if len(s1) > last_op[1]:
        yield s1[last_op[1]:], s2[last_op[2]:]


def subseq_matcher(seq1, seq2):
    """ Match similar lines """
    ls_grid = np.zeros((len(seq1), len(seq2)))
    for subseq1_index, subseq1 in enumerate(seq1):
        for subseq2_index, subseq2 in enumerate(seq2):
            ra = ratio(subseq1, subseq2)
            ls_grid[subseq1_index][subseq2_index] = ra if ra > 30 else 0
    max_val = np.argwhere(ls_grid == np.amax(ls_grid))
    while ls_grid[max_val[0][0]][max_val[0][1]] != 0.0:
        if len(max_val) != 1:
            max_val = [max_val[np.argmin([np.abs(x-y) for x, y in max_val])]]
        ls_grid[:, max_val[0][1]], ls_grid[max_val[0][0], :] = 0, 0
        ls_grid[max_val[0][0]][max_val[0][1]] = -1
        max_val = np.argwhere(ls_grid == np.amax(ls_grid))
    matched_seq = []
    if len(seq1) <= len(seq2):
        for col_id, col in enumerate(ls_grid.T):
            match = np.argwhere(col == -1)
            if len(match) == 0:
                matched_seq.append(["", seq2[col_id]])
            else:
                matched_seq.append([seq1[match[0][0]], seq2[col_id]])
            if col_id < len(seq1) and np.sum(ls_grid[col_id][:]) != -1:
                matched_seq.append([seq1[col_id], ""])
    else:
        for row_id, col in enumerate(ls_grid):
            match = np.argwhere(col == -1)
            if len(match) == 0:
                matched_seq.append([seq1[row_id], ""])
            else:
                matched_seq.append([seq1[row_id], seq2[match[0][0]]])
            if row_id < len(seq2) and np.sum(ls_grid.T[row_id, :]) != -1:
                matched_seq.append(["", seq2[row_id]])
    return matched_seq

if __name__=='__main__':
    seq1 = [line for line in Path('test_01.txt').open('r').read().split('\n') if line.strip() != ""]
    seq2 = [line for line in Path('test_02.txt').open('r').read().split('\n') if line.strip() != ""]
    matched_seq = subseq_matcher(seq1, seq2)
    fulltext = ""
    for matched_subseq in matched_seq:
        text = ""
        for glyphs in seq_align(*matched_subseq):
            if not glyphs[0]:
                text += "[color=00FFFF]" + glyphs[1] + "[/color]"
            elif not glyphs[1]:
                text += "[color=b39ddb]" + glyphs[0] + "[/color]"
            elif glyphs[0] != glyphs[1]:
                text += '[color=b39ddb]' + glyphs[0] + "[/color]" + "[color=00FFFF]" + glyphs[1] + "[/color]"
            else:
                text += glyphs[0]
        fulltext += text+'\n'
    Path('test.txt').open('w').write(fulltext)