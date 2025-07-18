from bleurt import score

scorer = score.BleurtScorer("D:/BLEURT-20")
print(scorer.score(
    references=["光合作用需要光照、水和CO2"],
    candidates=["植物通过吸收光能、水分和二氧化碳制造养分"]
))