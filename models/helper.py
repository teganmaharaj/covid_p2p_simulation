import numpy as np
import datetime

from utils import PREEXISTING_CONDITIONS

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

    return candidate_encounters, exposed_encounters

def conditions_to_np(conditions):
    conditions_encs = np.zeros((len(PREEXISTING_CONDITIONS),))

    for condition in conditions:
        probability = PREEXISTING_CONDITIONS[condition][0]
        conditions_encs[probability.id] = 1
    return conditions_encs


def symptoms_to_np(symptoms_day, all_symptoms, all_possible_symptoms):
    rolling_window = 14
    aps = list(all_possible_symptoms)
    symptoms_enc = np.zeros((rolling_window, len(all_possible_symptoms)+1))
    for day, symptoms in enumerate(all_symptoms[:14]):
        for symptom in symptoms:
            symptoms_enc[day, aps.index(symptom)] = 1.
    return symptoms_enc

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
    except IndexError:
        return rolling

def encode_age(age):
    if age is None:
        return -1
    else:
        return age

def encode_sex(sex):
    if not sex:
        return -1
    sex = sex.lower()
    if sex.startswith('f'):
        return 1
    elif sex.startswith('m'):
        return 2
    else:
        return 0
