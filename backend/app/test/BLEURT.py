from bleurt import score

scorer = score.BleurtScorer("D:/BLEURT-20")
print(scorer.score(
    references=[],
    candidates=[]
))