"""Mô hình co giãn số chuyên gia × số ngày theo Gms (YEU-CAU-FINAL mục 8)."""
import math


def round_half_up(x):
    return math.floor(x + 0.5)


def anchor_points(anchors, moc):
    return [(moc[i], a[0] * a[1]) for i, a in enumerate(anchors) if a]


def is_active(anchors, gms, ts):
    """Việc chỉ có ở M, L xuất hiện khi Gms ≥ ngưỡng M; chỉ có ở L khi Gms ≥ ngưỡng L."""
    if anchors[0]:
        return True
    if anchors[1]:
        return gms >= ts["nguong_M"]
    if anchors[2]:
        return gms >= ts["nguong_L"]
    return False


def raw_total(points, gms, exp):
    """Nội suy log-log giữa các mốc neo; ngoài khoảng neo co giãn theo hệ số exp."""
    if gms <= 0:
        return 0.0
    x0, t0 = points[0]
    xn, tn = points[-1]
    if gms <= x0:
        return t0 * (gms / x0) ** exp
    if gms >= xn:
        return tn * (gms / xn) ** exp
    for (xa, ta), (xb, tb) in zip(points, points[1:]):
        if xa <= gms <= xb:
            k = math.log(gms / xa) / math.log(xb / xa)
            return ta * math.exp(math.log(tb / ta) * k)
    return tn  # không xảy ra


def total_days(anchors, gms, ts):
    pts = anchor_points(anchors, ts["moc_neo"])
    return max(1, round_half_up(raw_total(pts, gms, ts["exp"])))


def experts_for(total, ladder):
    for i, b in enumerate(ladder):
        if total <= b:
            return i + 1
    return len(ladder) + 1


def split(total, ladder):
    e = experts_for(total, ladder)
    return e, math.ceil(total / e)
