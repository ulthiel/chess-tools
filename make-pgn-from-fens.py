#!/usr/bin/python3
#
# Reads in a text file of chess positions in FEN format (one by line) and creates a PGN file
# with these positions, extended by an engine main line. The event tag can be set to a
# common title; the round tag will be set to the line number. 
#
# Example: python3 make-pgn-from-fens.py input.txt output.pgn
# 
# A typical application is a collection of tactics positions scanned with a phone app from a
# book. The PGN can then be imported into, e.g., ChessBase or HIARCS Explorer for training.
#
# Some settings are set by the variables below.
#
# By Ulrich Thiel, 2023
import sys
import chess
import chess.engine
import chess.pgn
from tqdm import tqdm

# Set path to binary of engine
ENGINE_BIN = "../../Engines/Stockfish 16/bin/stockfish-16-mac-x86-64-bmi2"

# Seconds per position for analysis (can be a float)
SECS_PER_POS = 1

# Set to True if the winning probability (based on a WDL model, see below) should be added
# as comment after the final move of the pv.
ADD_PROB = True

# The WDL model. Needs to match the engine. 
# See https://python-chess.readthedocs.io/en/latest/engine.html#chess.engine.Score.wdl
WDL_MODEL = "sf16"

# Program starts here
if len(sys.argv) < 2:
    sys.exit("Please provide input filename as argument")

if len(sys.argv) < 3:
    sys.exit("Please provide output filename as argument")
    
infilename = sys.argv[1]
infile = open(infilename, 'r')
title = input("Title (Event tag): ")
board = chess.Board()
counter = 0
invalids = []
illposed = []

num_lines = 0
for line in infile.readlines():
    num_lines += 1

engine = chess.engine.SimpleEngine.popen_uci(ENGINE_BIN)

infile.seek(0)
outfilename = sys.argv[2]
outfile = open(outfilename, "w")
pbar = tqdm()
pbar.reset(total=num_lines)
for line in infile.readlines():
    counter = counter + 1
    board.reset()
    board.set_fen(line)
    if not board.is_valid():
        invalids.append(counter)
    info = engine.analyse(board, chess.engine.Limit(time=SECS_PER_POS))
    for move in info["pv"]:
        board.push(move)
    game = chess.pgn.Game().from_board(board)
    if title != "":
        game.headers["Event"] = title
    game.headers["Round"] = counter
    game.headers["Result"] = "*"
    node = game.end()

    if ADD_PROB:
        prob = info["score"].wdl(model=WDL_MODEL,ply=info["depth"]).white().expectation()
        node.comment = "p="+f"{prob:.2f}"

        # If the probability is close to a draw, the problem may be ill-posed
        if prob <= 0.55 and prob >= 0.45:
            illposed.append(counter)

    print(game, file=outfile, end="\n\n")
    pbar.update()

pbar.close()
engine.quit()

if len(invalids) > 0:
    print("Invalid positions: "+", ".join([str(i) for i in invalids]))

if len(illposed) > 0:
    print("Possibly ill-posed positions: "+", ".join([str(i) for i in illposed]))