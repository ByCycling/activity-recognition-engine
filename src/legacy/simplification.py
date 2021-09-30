import pandas as pd
from termcolor import colored

from app import app


def simplification(_input_df: pd.DataFrame) -> pd.DataFrame:
    _output_df = _input_df[
        # discard `still` positions, considered as noise
        (_input_df['activity.type'] != 'still') &
        # discard very inaccurate coordinates
        (_input_df['coordinates.coordinateAccuracy'] < 500)
        ].copy()

    # index by timestamp and sort
    _output_df = _output_df.set_index(pd.DatetimeIndex(_output_df['timestamp'].dt.tz_convert('UTC'))).sort_index()

    # remove duplicate indexes
    _output_df = _output_df[~_output_df.index.duplicated(keep='first')]

    _groups = _output_df.groupby(
        (_output_df['activity.type'] !=
         _output_df['activity.type'].shift())
            .cumsum()
    )

    if len(_groups) < 3: return _output_df

    app.logger.debug('{} type summary: {}'.format(colored('[starting simplification]', 'green'),
                                                  [x['activity.type'].iloc[0] for i, x in _groups]))

    for _index, _group in _groups:
        _current_type = _group['activity.type'].iloc[0]
        _current_size = len(_group)

        _previous_group = None
        _previous_type = None
        _previous_size = None

        _next_group = None
        _next_type = None
        _next_size = None

        # how big a chunk of activities should be in order to be retained in location data
        significance_threshold = 10
        # todo: use distance as threshold instead of point count
        _insignificant = _current_size < significance_threshold

        _avg_speed = (_group['coordinates.speed'] * 3.6).mean()
        # max average speed a person realistically can walk
        _max_avg_walking_speed = 6

        if _index > 1:
            _previous_group = _groups.get_group(_index - 1)
            _previous_type = _previous_group['activity.type'].iloc[0]
            _previous_size = len(_previous_group)

        if _index < len(_groups) - 1:
            _next_group = _groups.get_group(_index + 1)
            _next_type = _next_group['activity.type'].iloc[0]
            _next_size = len(_next_group)

        def simplify(replacement: str = None):
            if replacement is None:
                if _previous_type:
                    replacement = _previous_type
                elif _next_type:
                    replacement = _next_type
                else:
                    raise ValueError('cannot simplify: no type definitions')

            log(text='changing {} to {} on index {}'.format(_current_type, replacement, _index), tag='simplification',
                color='yellow')
            for __index, _x in _group.iterrows():
                _output_df.at[__index, 'activity.type'] = replacement

        def surrounded_by(_type: str):
            if _previous_type and _next_type:
                log(text='{} preceded by previous: {} and followed next: {}'.format(_current_type, _previous_type,
                                                                                    _next_type), tag='surrounded',
                    color='blue')
                return _previous_type == _type and _next_type == _type
            elif _next_type:
                log(text='{} followed by next: {}'.format(_current_type, _next_type), tag='surrounded', color='blue')
                return _next_type == _type
            elif _previous_type:
                log(text='{} preceded by previous: {}'.format(_current_type, _previous_type), tag='surrounded',
                    color='blue')
                return _previous_type == _type
            else:
                raise ValueError('cannot compare surrounding value: no type definitions')

        def on_foot():
            return _current_type == 'on_foot' or _current_type == 'walking'

        def log(tag: str, color: str, text: str):
            app.logger.debug('{tag} {text}'.format(tag=colored('[{}]'.format(tag), color), text=text))

        if on_foot() and surrounded_by('in_vehicle') and _avg_speed > _max_avg_walking_speed:
            log(text='walking surrounded by in_vehicle with average speed of {}'.format(_avg_speed), tag='case',
                color='magenta')
            simplify('in_vehicle')
            continue
        elif on_foot() and surrounded_by('on_bicycle') and _avg_speed > _max_avg_walking_speed:
            log(text='walking surrounded by on_bicycle with average speed of {}'.format(_avg_speed), tag='case',
                color='magenta')
            simplify('on_bicycle')
            continue
        elif _current_type == 'in_vehicle' and surrounded_by('on_bicycle'):
            log(text='in_vehicle surrounded by on_bicycle', tag='case', color='magenta')
            simplify('on_bicycle')
            continue
        elif _insignificant:
            log(text='fall-through to insignificant', tag='insignificant', color='red')
            simplify()
            continue

    app.logger.debug(colored('[simplification completed]', 'green'))
    return _output_df
