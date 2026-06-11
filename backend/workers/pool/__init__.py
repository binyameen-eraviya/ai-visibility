"""Account and proxy pool managers (Milestones 2 and 4).

account_pool: checkout/return/cooldown of free AI platform accounts,
quota tracking, auto-disable of banned accounts.
proxy_pool: same pattern for proxies, matched to the job's target country
(interface first, direct connections until a proxy plan is added).
"""
