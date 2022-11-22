query_format = """query ($params: Date!) {
  championshipsAgenda(filter: {date: $params}) {
    championship {
      name
      __typename
    }
    now: items(filter: {moment: NOW}) {
      __typename
      ...matchData
    }
    past: items(filter: {moment: PAST}) {
      __typename
      ...matchData
    }
    future: items(filter: {moment: FUTURE}) {
      __typename
      ...matchData
    }
    __typename
  }
}

fragment matchData on SoccerEvent {
  match {
    scoreboard {
      away
      home
      penalty {
        home
        away
        __typename
      }
      __typename
    }
    awayTeam {
      id
      popularName
      badge_svg: badge(format: "svg")
      badge_png: badge(format: "30x30")
      __typename
    }
    homeTeam {
      id
      popularName
      badge_svg: badge(format: "svg")
      badge_png: badge(format: "30x30")
      __typename
    }
    startDate
    startHour
    round
    winner {
      id
      __typename
    }
    phase {
      name
      type
      __typename
    }
    transmission {
      __typename
      ... on TRTransmission {
        id
        broadcastStatus {
          id
          label
          __typename
        }
        period {
          id
          label
          __typename
        }
        url
        __typename
      }
    }
    __typename
  }
  __typename
}
"""
