import numpy as np
import datetime
from collections import Counter
from models.utils import decode_message

def messages_to_np(human):
    ms_enc = []
    for day, clusters in human.clusters.clusters_by_day.items():
        for cluster_id, messages in clusters.items():
            # TODO: take an average over the risks for that day
            if not any(messages):
                continue
            ms_enc.append([cluster_id, decode_message(messages[0]).risk, len(messages), day])
    return np.array(ms_enc)

def candidate_exposures(human, date):
    candidate_locs = list(human.locations_visited.keys())
    exposed_locs = np.zeros(len(candidate_locs))
    if human.exposure_source in candidate_locs:
        exposed_locs[candidate_locs.index(human.exposure_source)] = 1.
    candidate_encounters = messages_to_np(human)
    exposed_encounters = np.zeros(len(candidate_encounters))
    if human.exposure_message and human.exposure_message in human.clusters.all_messages:
        idx = 0
        for day, clusters in human.clusters.clusters_by_day.items():
            for cluster_id, messages in clusters.items():
                for message in messages:
                    if message == human.exposure_message:
                        exposed_encounters[idx] = 1.
                        break
                if any(messages):
                    idx += 1

    return candidate_encounters, exposed_encounters, candidate_locs, exposed_locs


def symptoms_to_np(symptoms_day, all_symptoms, all_possible_symptoms):
    rolling_window = 14
    aps = list(all_possible_symptoms)
    symptoms_enc = np.zeros((rolling_window, len(all_possible_symptoms)+1))
    for day, symptoms in enumerate(all_symptoms[:14]):
        for symptom in symptoms:
            symptoms_enc[day, aps.index(symptom)] = 1.
    return symptoms_enc

def group_to_majority_id(all_groups):
    all_new_groups = []
    for group_idx, groups in enumerate(all_groups):
        new_groups = {}
        for group, uids in groups.items():
            cnt = Counter()
            for idx, uid in enumerate(uids):
                cnt[uid] += 1
            for i in range(len(cnt)):
                new_groups[cnt.most_common()[i][0]] = uids
                break
        all_new_groups.append(new_groups)
    return all_new_groups

def rolling_infectiousness(start, date, human):
    rolling_window = 14
    rolling = np.zeros(rolling_window)
    if human.infectiousness_start_time == datetime.datetime.max:
        return rolling
    cur_day = (date - start).days

    hinf = []
    for v in human.infectiousness.values():
        if type(v) == float:
            hinf.append(v)
        elif type(v) == np.ndarray:
            hinf.append(v[0])

    if not human.infectiousness:
        return rolling

    rollings = []
    for end in range(1, len(hinf) + 1):
        if end - rolling_window > 0:
            start = end - rolling_window
            rolling = np.flip(hinf[start:end])
        else:
            rolling = np.flip(hinf[:end])
        rolling = np.pad(rolling, (0, rolling_window - len(rolling)))
        rollings.append(rolling)
    human.rolling_infectiousness_array = rollings

    try:
        return rollings[cur_day]
    except Exception:
        return rolling
