import numpy as np


# Participant Sentiment Parameters
sentiment_decay = 0.005
sentiment_sensitivity = 0.75
candidate_proposals_cutoff = 0.75
delta_holdings_scale = 70000
sentiment_bonus_proposal_becomes_active = 0.5
sentiment_bonus_proposal_becomes_completed = 0.3
sentiment_bonus_proposal_becomes_failed = -0.1
engagement_rate_multiplier_buy = 0.6
engagement_rate_multiplier_sell = 0.6
engagement_rate_multiplier_exit = 0.3
sentiment_sensitivity_exit = 0.5

# Participant Investment Parameters
investment_new_participant_min = 0.0
investment_new_participant_stdev = 100

# Speculator Parameters
speculator_position_size_min = 200  # DAI
speculator_position_size_stdev = 200
speculators = 5

# Proposal Parameters
min_age_days = 2
scale_factor = 0.01
base_failure_rate = 0.15
base_success_rate = 0.30
funds_requested_alpha = 3
funds_requested_min = 0.001

# Trigger threshold Parameters
rho_multiplier = 0.5
rho_power = 2

# Vesting curve Parameters
vesting_curve_halflife = 0.5
log_base05_of_02 = 2.321928094887362

# GenerateNewParticipant Parameters
arrival_rate_denominator = 10
max_new_participants = 1

# Speculation vesting
speculation_days = 24 + int(72 * np.random.rand())
multiplier_new_participants = 1 + int(9 * np.random.rand())
