from trueskill import rate, TrueSkill


def processRanks(playerInfos):
    env = TrueSkill()
    playerScores = [p.score for p in playerInfos]
    matchRanks = [sorted(playerScores, reverse=True).index(x) for x in playerScores]
    ratings = {}

    for info in playerInfos:
        if not info.rating:
            info.rating = env.create_rating()
    ratings = [{p: p.rating} for p in playerInfos]
    # ratings = [{playerInfos[0]: playerInfos[0].rating}, {playerInfos[1]: playerInfos[1].rating}]
    ranks = rate(ratings, matchRanks)
    result = []
    for rank_dict in ranks:
        for playerInfo in rank_dict:
            rank = rank_dict[playerInfo]
            playerInfo.rank = rank.mu - 3 * rank.sigma
            playerInfo.mu = rank.mu
            playerInfo.sigma = rank.sigma
            result.append(playerInfo)
    return sorted(result, key=lambda player: -player.rank)
