import csv
import random
import os
from threading import RLock

class Quotes:
  __lock = RLock()
  quotes = []

  # load quotes into array
  def _init_quotes():
    try:
      Quotes.__lock.acquire()
      if len(Quotes.quotes) > 0:
        return
      # use ENV specified quote file if available
      quote_file = os.environ.get('QUOTE_FILE')
      if not quote_file:
        quote_file = "/quotes/quotes.csv"
      with open (quote_file, "r", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
          if row:
            Quotes.quotes.append(row)
    finally:
      Quotes.__lock.release()

  def get_one_quote():
    try:
      Quotes._init_quotes()
      i = random.randint(1, len(Quotes.quotes)-1)
      quote = Quotes.quotes[i]
      lines = []
      for line in quote:
        line = line.strip()
        if not line:
          continue
        formatted_lines = line.split('¶')
        for formatted_line in formatted_lines:
          if formatted_line:
            lines.append(formatted_line)
      return lines
    except Exception as e:
      return [f"Failed to get quote: {e}"]