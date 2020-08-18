import csv
import random
from threading import RLock

class Quotes:
  __lock = RLock()
  quotes = []

  # load quotes into array
  def init_quotes(quotes_csv):
    try:
      Quotes.__lock.acquire()
      if len(Quotes.quotes) > 0:
        return
      with open (quotes_csv, "r", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
          Quotes.quotes.append(row)
    finally:
      Quotes.__lock.release()

  def get_one_quote():
    i = random.randint(1, len(Quotes.quotes))
    quote = Quotes.quotes[i]
    lines=[]
    for line in quote:
      line=line.strip()
      if (line):
        lines.append(f"{line}\n")
    return lines
