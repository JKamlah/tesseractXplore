import numpy as np
from rapidfuzz.string_metric import levenshtein_editops
from rapidfuzz.fuzz import ratio

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
            if op[1] != 0 and op[2] != 0:
                yield s1[:op[1]], s2[:op[2]]
            last_op = op
        if op[0] == "insert":
            if last_op[0] != op[0] or last_op[1] != op[1]:
                yield report(last_op, seq1, seq2)
                if last_op[1] < op[1]:
                    yield s1[last_op[1]:op[1]], s2[last_op[2]:op[2]]
                seq1, seq2 = "", ""
            seq2 += s2[op[2]]
            op = (op[0], op[1], (op[2]+1))
        elif op[0] == "delete":
            if last_op[0] != op[0] or last_op[2] != op[2]:
                yield report(last_op, seq1, seq2)
                if last_op[2] < op[2]:
                    yield s1[last_op[1]:op[1]], s2[last_op[2]:op[2]]
                seq1, seq2 = "", ""
            seq1 += s1[op[1]]
            op = (op[0], (op[1]+1), op[2])
        elif op[0] == "replace":
            if last_op[0] != op[0] or last_op[1] < op[1]:
                yield report(last_op, seq1, seq2)
                if last_op[1] < op[1]:
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
    unmatched_col = []
    for col_id, col in enumerate(ls_grid.T):
        if not np.sum(col):
            unmatched_col.append(col_id)
    for row_id, row in enumerate(ls_grid):
        match = np.argwhere(row == -1)
        if len(match) == 0:
            matched_seq.append([seq1[row_id], ""])
        else:
            matched_seq.append([seq1[row_id], seq2[match[0][0]]])
        if row_id < len(seq2) and np.sum(ls_grid.T[row_id, :]) != -1:
            matched_seq.append(["", seq2[row_id]])
        if row_id in unmatched_col:
            matched_seq.append(["", seq2[unmatched_col.pop()]])
    matched_seq.extend([["", seq2[col_id]] for col_id in unmatched_col])
    return matched_seq
