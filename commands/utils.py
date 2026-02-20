from database import c

def fetched_combinations(sound_combinations, results, c, server_id):
    """Fetch combination details from database"""
    for row in results:
        sound_ids = []
        query = "SELECT sound_id FROM sound_combination_sounds WHERE combination_id = (SELECT id FROM sound_combination WHERE server_id = %s AND sound_name = %s)"
        c.execute(query, (server_id, row[0]))
        sound_combination_ids = c.fetchall()
        for ids in sound_combination_ids:
            sound_ids.append(ids[0])
        sound_combinations[row[0]] = sound_ids
    return sound_combinations
