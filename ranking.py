from trueskill import rate, TrueSkill


def processRanks(playerInfos):
    env = TrueSkill()
    playerScores = [p.score for p in playerInfos]
    matchRanks = [sorted(playerScores, reverse=True).index(x) for x in playerScores]
    print(matchRanks)
    ratings = {}

    for info in playerInfos:
        if not info.rating:
            info.rating = env.create_rating()
    ratings = [{p: p.rating} for p in playerInfos]
    # ratings = [{playerInfos[0]: playerInfos[0].rating}, {playerInfos[1]: playerInfos[1].rating}]
    return rate(ratings, matchRanks)
