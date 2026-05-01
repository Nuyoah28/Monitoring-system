from dataclasses import dataclass


@dataclass
class ActionFSMConfig:
    fall_on_thr: float = 0.35
    fall_off_thr: float = 0.15
    fall_hold_frames: int = 75
    fall_release_frames: int = 30
    fall_latch: bool = False

    wave_on_thr: float = 0.45
    wave_off_thr: float = 0.25
    wave_confirm_frames: int = 4
    wave_release_frames: int = 10

    punch_on_thr: float = 0.45
    punch_off_thr: float = 0.20
    punch_confirm_frames: int = 3
    punch_release_frames: int = 8

    fight_confirm_frames: int = 4
    fight_release_frames: int = 12
    fight_distance_ratio: float = 1.4


class TrackActionFSM:
    def __init__(self, config: ActionFSMConfig):
        self.cfg = config
        self._state = {}

    def pop(self, track_id):
        self._state.pop(track_id, None)

    def _get_state(self, track_id):
        if track_id not in self._state:
            self._state[track_id] = {
                "fall_hold_left": 0,
                "fall_low_count": 0,
                "fallen_state": False,
                "fall_event": False,
                "wave_on_count": 0,
                "wave_off_count": 0,
                "wave_help": False,
                "punch_on_count": 0,
                "punch_off_count": 0,
                "punch_candidate": False,
                "fight_on_count": 0,
                "fight_off_count": 0,
                "fight_confirmed": False,
            }
        return self._state[track_id]

    def update(self, track_id, probs, has_nearby_person=False):
        st = self._get_state(track_id)
        fall_prob = float(probs.get("fall", 0.0))
        wave_prob = float(probs.get("wave", 0.0))
        punch_prob = float(probs.get("punch", 0.0))

        self._update_fall(st, fall_prob)
        self._update_wave(st, wave_prob)
        self._update_punch(st, punch_prob, has_nearby_person)

        return {
            "fall": bool(st["fallen_state"]),
            "fall_event": bool(st["fall_event"]),
            "fallen_state": bool(st["fallen_state"]),
            "wave": bool(st["wave_help"]),
            "wave_help": bool(st["wave_help"]),
            "punch": bool(st["fight_confirmed"]),
            "punch_candidate": bool(st["punch_candidate"]),
            "fight_confirmed": bool(st["fight_confirmed"]),
            "fall_prob": fall_prob,
            "wave_prob": wave_prob,
            "punch_prob": punch_prob,
        }

    def _update_fall(self, st, fall_prob):
        st["fall_event"] = fall_prob >= self.cfg.fall_on_thr

        if st["fallen_state"]:
            if self.cfg.fall_latch:
                st["fall_hold_left"] = self.cfg.fall_hold_frames
                st["fall_low_count"] = 0
                return

            st["fall_hold_left"] = max(0, st["fall_hold_left"] - 1)
            if fall_prob < self.cfg.fall_off_thr:
                st["fall_low_count"] += 1
            else:
                st["fall_low_count"] = 0

            if (
                st["fall_hold_left"] == 0
                and st["fall_low_count"] >= self.cfg.fall_release_frames
            ):
                st["fallen_state"] = False
                st["fall_low_count"] = 0
        elif fall_prob >= self.cfg.fall_on_thr:
            st["fallen_state"] = True
            st["fall_hold_left"] = self.cfg.fall_hold_frames
            st["fall_low_count"] = 0

    def _update_wave(self, st, wave_prob):
        if wave_prob >= self.cfg.wave_on_thr:
            st["wave_on_count"] += 1
            st["wave_off_count"] = 0
        elif wave_prob < self.cfg.wave_off_thr:
            st["wave_off_count"] += 1
            st["wave_on_count"] = 0

        if st["wave_on_count"] >= self.cfg.wave_confirm_frames:
            st["wave_help"] = True

        if st["wave_help"] and st["wave_off_count"] >= self.cfg.wave_release_frames:
            st["wave_help"] = False
            st["wave_off_count"] = 0

    def _update_punch(self, st, punch_prob, has_nearby_person):
        if punch_prob >= self.cfg.punch_on_thr:
            st["punch_on_count"] += 1
            st["punch_off_count"] = 0
        elif punch_prob < self.cfg.punch_off_thr:
            st["punch_off_count"] += 1
            st["punch_on_count"] = 0

        if st["punch_on_count"] >= self.cfg.punch_confirm_frames:
            st["punch_candidate"] = True

        if st["punch_candidate"] and st["punch_off_count"] >= self.cfg.punch_release_frames:
            st["punch_candidate"] = False
            st["punch_off_count"] = 0

        if st["punch_candidate"] and has_nearby_person:
            st["fight_on_count"] += 1
            st["fight_off_count"] = 0
        else:
            st["fight_off_count"] += 1
            st["fight_on_count"] = 0

        if st["fight_on_count"] >= self.cfg.fight_confirm_frames:
            st["fight_confirmed"] = True

        if st["fight_confirmed"] and st["fight_off_count"] >= self.cfg.fight_release_frames:
            st["fight_confirmed"] = False
            st["fight_off_count"] = 0
