"""
 Script will run scoring algorithms against set of csv input comaprisons

 Excepts:
 - input file to be named input.csv in scripts folder
 - input file rows to be stuctured: "key1, key2, winning_key"

 Outputs:
 - for every algorithms: file named 'out'+algorithm name+'.csv' in the scripts folder
 - output file rows are structured "id, score, rounds, wins, normalized score"

"""
import csv
import os

from acj.algorithms import ComparisonPair, ScoredObject
from acj.algorithms.score import calculate_score
from acj.models.score_algorithm import ScoringAlgorithm

KEY1 = 0
KEY2 = 1
WINNING_KEY = 2

CURRENT_FOLDER = os.getcwd() + '/scripts'

comparisons = []

with open(CURRENT_FOLDER+'/input.csv', 'rU') as csvfile:
    spamreader = csv.reader(csvfile)
    for row in spamreader:
        if row:
            comparisons.append(ComparisonPair(
                int(row[KEY1]), int(row[KEY2]), int(row[WINNING_KEY])
            ))

packages = [
    ScoringAlgorithm.comparative_judgement.value,
    ScoringAlgorithm.elo.value,
    ScoringAlgorithm.true_skill.value
]
for package_name in packages:
    results = calculate_score(
        package_name=package_name,
        comparison_pairs=comparisons
    )

    with open(CURRENT_FOLDER+"/out_"+package_name+".csv", "w+") as csvfile:
        out = csv.writer(csvfile)

        out.writerow(["id", "score", "rounds", "wins", "normal score"])

        for key, result in results.items():
            out.writerow([result.key, result.score,
                result.rounds, result.wins, ""])


