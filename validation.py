def validate_beam_length(beam_length):
    return beam_length > 0


def validate_position(position, beam_length):
    return 0 <= position <= beam_length


def validate_direction(direction):
    return direction in ["U", "D"]