import datetime
import re
import unicodedata
from urllib import request
from functools import reduce


def getCSV(hash: str):
    url = f"https://chouseisan.com/schedule/List/createCsv?h={hash}"
    res = request.urlopen(url)
    if res.getcode() != 200:
        return
    content = res.read()
    csvData = content.decode()
    return csvData


def csv2data(csvData: str):
    raw = csvData.split("\n")
    title = raw[0]
    header = raw[2].split(",")[1:]

    def pickNames(acc: list, day: tuple[int, str]):
        if day[1] == "◯":
            acc.append(header[day[0]])
        return acc

    signData = list(map(lambda r: r.split(","), raw[3:-2]))
    data = list(
        map(lambda d: (toDate(d[0]), reduce(pickNames, enumerate(d[1:]), [])), signData)
    )
    return title, data


def isChouseisanUrl(url: str):
    pattern = "^https?://chouseisan.com/s\\?h=\\w+$"
    res = re.fullmatch(pattern, url)
    return bool(res)


def getHash(url: str):
    if not isChouseisanUrl(url):
        return
    pattern = "\\?h=(\\w+)"
    hash = re.search(pattern, url).group(1)
    return hash


def toDate(dateStr: str):
    normalized = unicodedata.normalize("NFKC", dateStr)
    pattern = "\\d+"
    month, day, *_ = [int(d.group()) for d in re.finditer(pattern, normalized)]
    today = datetime.date.today()
    sameYearDate = datetime.date(today.year, month, day)
    thresh = 152
    yearDiff = (
        1
        if (today - sameYearDate).days > thresh
        else -1
        if (sameYearDate - today).days > thresh
        else 0
    )
    date = datetime.date(today.year + yearDiff, month, day)
    return date
