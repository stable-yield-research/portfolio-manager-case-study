<!--
All report text lives in this file. Each block starts with "## key" and runs until the next "## ".
Edit freely. Words in {braces} are filled with computed numbers: keep the braces, move them around as you like.
Use \$ for a dollar sign. Blank line = new paragraph.
-->

## report.title
Stablecoin Carry on Current Finance: Allocation Proposal

## report.subtitle
Investment memorandum · October 2026 · Current Finance data to {data_date}

## report.disclosure
Performance figures are reconstructed from public on-chain and protocol data at the stated position sizes. They are not the record of a live book. Small live pilots confirmed the mechanics, including reward payouts. The sourcing framework, risk checklist, process manual and dashboard tooling behind this report were built before the case study. The work this week went into applying them to current opportunities and running the analysis.

## summary.lead
I recommend putting \$1.5M, about 4% of the fund, into a leveraged USDC and USDSUI carry on Current Finance (current.finance), a lending platform on Sui, at 3.5 times leverage. In September it earned about 15% a year after costs at that size, from lending interest and SUI rewards net of borrowing costs. The USDSUI the fund holds equals the USDSUI it owes, so its capital stays in USDC with no net exposure to USDSUI's price. Only a USDSUI move of 16% or more would force a sale. SUI rewards are sold or hedged daily.

## summary.positioning
This is a small, higher-risk position next to the fund's simpler stablecoin holdings. I left out the well-known options, such as lending on Aave and Morpho or fixed-rate products on Pendle, because I assume the team already uses them and their returns tend to fall quickly as more money arrives. Positions that earn more than 12% at this size are rare today without automated trading. This one needs no automation, but it takes more steps than plain lending, so I would keep it small and set the exit rules in advance.

The table at the end of this page shows where each question in the case study brief is answered.

## summary.s1.oneliner
In plain terms: the fund deposits USDC, borrows USDSUI against it, swaps the USDSUI into USDC and deposits that as well. Doing this until the deposits are 3.5 times the fund's own money is the leverage. A second, mirror-image position deposits USDSUI and borrows USDC. The USDSUI the fund owes in the first position equals the USDSUI it holds in the second, so small changes in USDSUI's price cancel out. Each position on its own is still exposed, which is why a USDSUI move of 16% or more would force the sale of one of them.

The fund earns interest and SUI rewards on everything it deposits, and pays interest on what it borrows. The difference is the return. On Current Finance each position is a "Multiply vault", a tool that builds the leveraged position in a single transaction.

## summary.why
Most active curators and allocators work on EVM networks and Solana. Sui is not EVM-compatible, so their integrations, tooling and infrastructure do not carry over and have to be built from scratch, and few funds have done that. Current Finance only launched in March 2026, so many funds have not yet approved it. The position also takes more work than a single deposit. Together these keep the return higher than on the better-known platforms.

Most of my time went into the risks. I measured how Current Finance's interest rates move using its own hourly data, checked who controls the platform and its code, worked out the cost of getting out, and set the leverage from USDSUI's actual price history rather than from the maximum the platform allows.

## summary.risk
1. The biggest risk is a hack of Current Finance. If an attacker found a flaw, Current Finance could freeze withdrawals and the fund could not get its money out quickly. The code has been reviewed by five security firms and in a public contest, and every serious finding was fixed. Outside firms review every change to the code and settings, and a change to the settings must wait a day after it is proposed before it takes effect. A monitoring firm watches for attacks in real time, and daily withdrawal limits slow down any theft. Insurance is available from Nexus Mutual, but at about 4.3% a year it would cost too much of the return. In the end, the small size of the position is what limits the damage.
2. The second risk is a stablecoin losing its dollar value, or a wrong price reaching the platform. The fund's positions would only be forcibly closed (liquidated) if USDSUI moved about {liq_dn_plain} to {liq_up_plain} against USDC. Its largest move so far is 1.3%. Bridge exchanges USDSUI for dollars one to one, and Current Finance ignores any price more than 5% away from one dollar, so a wrong price cannot cause a liquidation. One specific risk: Bridge creates new USDSUI with a single key. If that key were stolen, the thief could create USDSUI with nothing behind it and use it to borrow real USDC from the pool the fund lends into. Current Finance's daily borrowing limit would cap the fund's loss at about 7% of its money in a day.
3. The third risk is a cut in the SUI rewards. A cut of 15% would take the return below 12%. I would check the reward rate every day and exit if a cut lasted two weeks.

## summary.alternatives
The simplest alternative is to lend USDC on Current Finance without leverage, which pays about 8.3% with the same platform risk. The leveraged position adds about 6.4 points in exchange for the risk of a forced sale if USDSUI moved 16% or more, and some sensitivity to USDSUI interest rates. Apart from the two strategies on hold, I looked at {n_screened} other opportunities. The stablecoin positions advertising 20% to 30% elsewhere do not have enough borrowing room for \$1.5M. The others fell short on size, ease of exit or where the return comes from. The screening page lists them all, including those that could work with automation or a longer record.

## summary.run
I would build the position in batches of \$150,000 to \$300,000, as fast as the market allows without moving USDSUI's price. Current Finance limits new USDSUI borrowing to \$0.7M a day across all users, so this takes three to four days. To keep entry costs down, the fund can receive USDC on Sui directly from an exchange or through a bridge, and, with an account at Bridge, can create USDSUI one to one instead of buying it on the market.

Leverage starts at 3.5 times. I would rebalance once a month, because interest slowly eats into the safety margin, and would only consider going up to 4.5 times after six to twelve months without problems, an independent review of the price feed and insurance at a reasonable price.

The SUI rewards would be claimed every day and either sold or protected against a fall in price with a short futures position.

The size of the position depends on how quickly it can be closed. Today about \$1M of USDSUI can be exchanged for USDC at a cost below 0.03%, so the whole position can be closed in a few batches. If that becomes more expensive, I would reduce the position. Closing costs are set aside at {exit_prov} and tested at {exit_stress} in a bad market.

## summary.verdict
Current Finance can take \$1.5M today at about {cur_sep} a year after costs, with the fund's money kept in dollar stablecoins. It is a small position at the riskier end of the fund and needs close watching. On those terms I am comfortable running it.

## s1.structure
The strategy uses two positions on Dolomite, on Ethereum mainnet.

| | Supplies | Borrows |
| --- | --- | --- |
| Position A | USDC | USD1 |
| Position B | The USD1 borrowed in A | USDC, which goes back into A |

The USD1 supplied equals the USD1 borrowed, so a move in USD1's price cancels out and the net exposure is the fund's equity in USDC. The WLFI campaign pays on USD1 supply minus borrowing of other listed assets. Keeping the USD1 supply apart from the USDC debt keeps the whole supply eligible, and a live pilot on 29 September confirmed this. Rewards would be claimed weekly and sold for USDC, with any unsold balance hedged with a short WLFI perpetual.

## s1.yield_note
The lending spread on its own is negative, and the return comes from the WLFI rewards. Every basis point traces back to a Dolomite interest index or a reward payout.

## s1.audit
Returns are rebuilt from the same numbers a live position earns: Dolomite's interest indexes (the exact growth a lender or borrower received each day), the daily WLFI reward rate, and the WLFI price for the guardrails. Scripts and data are included, so every figure can be reproduced.

## s1.entry
Entry needs no market trades. USDC goes into position A, USD1 is borrowed and moved to position B as collateral, and USDC is borrowed in B and added back to A. The steps repeat until the target leverage is reached, with both positions at equal health. Everything happens on Dolomite's ledger, so there is no swap and no slippage. The only cost is gas.

## s1.liquidity_note
To test before funding: netting USD1 supply against USD1 debt across the two positions without pool liquidity. This is the fast exit if the pools freeze.

## s1.stress_note
The shortfall is the debt minus the collateral value when no liquidation fills. It is split according to each position's debt mix and shared in proportion. In a run, whoever withdraws first is paid in full, so real losses land unevenly. Exiting early matters more than the average suggests.

## s1.liquidators
Liquidators would clear part of this collateral, but not all of it. On 29 and 30 September the market looked like this.

| Venue | Depth |
| --- | --- |
| Spot exchanges | About \$8.2M of bids within 2% of the price, and about \$38M of daily volume |
| Perpetual futures | About \$369M of open interest and \$138M of daily volume, with \$136M of open interest on Binance alone |
| Ethereum DEXs | About \$6.7M of liquidity (WLFI/ETH \$4.2M, WLFI/USDT \$1.4M, WLFI/USDC \$1.2M) |
| Solana | The large Raydium WLFI/USDC position (about \$55M) is almost all WLFI. It is a sell wall above the price and adds no bids. |

Perpetuals are the largest buffer. An arbitrageur can buy discounted WLFI from a liquidation, short the perpetual to lock in the price and sell the spot over hours or days. Even so, the largest pure-WLFI position would need about \$48M of WLFI sold, so the stress table shows losses under several liquidation capacities rather than one.

## s1.record
Between February and April 2026, World Liberty Financial's treasury borrowed stablecoins against WLFI on Dolomite, and Dolomite raised the WLFI supply cap to 5.1B tokens to fit it. The USD1 pool then reached 100% utilization: almost everything supplied had been borrowed, so ordinary depositors could not withdraw until loans were repaid or new supply arrived. This was a liquidity squeeze from heavy borrowing, not a hack. After public scrutiny in April, World Liberty Financial repaid \$25M and said it would add collateral if needed. No structural change followed: no insurance fund, no cap reduction, no parameter change.

## s1.team
Before funding, I would want the team to look at every attack path, not just the strategy's own contracts.

| Area | What I would ask for |
| --- | --- |
| Smart contracts and forensics | Dolomite's margin and admin contracts (a 2-of-3 Safe with a 5-minute timelock), USD1's mint and freeze roles, the reward contract, and how liquidations and internal transfers behave in a fully used pool. |
| Keys | The fund's signer setup, hardware keys, a Roles Modifier allowlist so each key can only make the calls each strategy needs, and monitoring of the fund's Safe for unexpected changes. |
| Signing | Simulation and decoding of every transaction before signing, protection against spoofed or poisoned addresses, and no blind signing through a web interface. |
| Legal and compliance | The regulatory and reputational exposure to USD1 and WLFI, and how WLFI rewards are treated. |
| Trading | Selling rewards, hedging WLFI, and running the unwind at size. |
| Risk | An independent check of the stress model and the trigger levels. |

## s1.why
About {wl_share} of the USD1 borrowed on Dolomite is backed by WLFI. Many desks will not lend next to an issuer's loan against its own token, which keeps supply thin and rewards high.

The strategy also only works with the two-position structure. Without rewards the carry is {base_only} at 3x, and a single-position loop loses part of the reward. Some mandates exclude reward-driven yield altogether. Capacity is limited as well, since the rewards dilute as more supply arrives.

## s1.premortem
The most likely way this loses money is a fast WLFI crash that freezes the USD1 and USDC pools before the position is reduced. Liquidators cannot sell the WLFI, the pools take bad debt, and the position is still at 3x when withdrawals stop. A 90% fall in WLFI would cost about {loss90} of equity, or {loss90_net} after netting the two positions.

The second is that WLFI rewards end or are cut, the carry turns negative and the exit comes too late.

Acting on the first day a WLFI or pool trigger fires, testing the netting step in advance and keeping a hard cap on size would limit both.

## s2.structure
The strategy has three steps.

1. Deposit crvUSD on Resupply. It is lent in Curve Lend's sfrxUSD market and earns that lending rate.
2. Borrow reUSD against it. Resupply pays borrowers rewards in CRV, RSUP and CVX on top of the borrow cost.
3. Provide the reUSD as liquidity in the Curve reUSD/scrvUSD pool through Stake DAO, earning trading fees and boosted CRV.

The pool holds about {re_share} reUSD. Borrowing the reUSD that goes into the pool cancels most of the depeg exposure. The scrvUSD side remains.

## s2.lp_yield
The pool pays trading fees of about 1% and CRV emissions. Stake DAO deposits earn CRV at a 2.38x boost, close to Curve's 2.5x maximum, and Stake DAO keeps 15.5% as fees. Today that comes to 16.8% in CRV plus 1% in fees, 17.8% in total.

For earlier days the model rebuilds the same figure from the pool's unboosted CRV rate, which matches today's reading within 0.1 point. CRV emissions to this pool rose in August. For most of the previous year the boosted CRV rate was 4.6% to 8%, so the current level depends on gauge votes holding up.

## s2.variants
There are three ways to hold the position. Buying reUSD and scrvUSD outright keeps the fund's capital out of Resupply's contracts, but leaves the fund long about three-quarters reUSD. When reUSD drifted from 0.990 to 0.984 over the last month, that cost about 5.6 points of annualized yield.

Funding the reUSD with a Resupply loan removes that exposure and adds the borrow rewards, but it puts the fund's crvUSD collateral inside a protocol that was exploited in 2025 and has published no audit since. Splitting half and half halves both effects. Holding reUSD outright does not avoid Resupply risk either, because reUSD is Resupply's own liability. A protocol failure would reach the fund through the price instead of the collateral.

## s2.venues
The LP is staked through Stake DAO. The same pool is also available as an autocompounding vault on Beefy, which stakes through Convex. Beefy saves the weekly reward claims, but it yields less (16.5% after fees) and adds two more contract layers.

## s2.depeg
The Curve pool uses the StableSwap formula with an amplification of 200. Prices stay close to par much longer than in a constant-product pool, and when reUSD weakens, arbitrage adds reUSD to the pool.

Because all the reUSD that goes into the pool is borrowed, and the pool is only about three-quarters reUSD, the position starts slightly short reUSD. A depeg therefore produces a small gain. As it deepens, the LP collects more reUSD, which brings the fund's reUSD holdings back towards its debt. The cost is on the other side, if reUSD recovers to 1.00 or above. Borrowing only the pool's reUSD share would make the position neutral at today's mix, but small losses would then come in both directions.

## s2.il
Compared with simply holding the tokens deposited, the pool loses little near par: 0.01% at 0.985 and 0.12% at 0.97. The loss then grows as the pool fills with reUSD, to 1.2% at 0.90 and 3.5% at 0.80. The LP also ends up holding more reUSD as the price falls, up to a quarter more at 0.80.

For a plain LP this adds to the price loss. A slide from 0.990 to 0.985 already costs 0.3% of equity. In this structure the extra reUSD is matched by the reUSD owed, which is why a depeg nets out as a small gain.

## s2.exit_rules
The fund aims for a positive result every month, so the position may give back at most what it has already earned. The mark-to-market loss is capped at 0.3% of equity, about one week of income at the current yield. The exit runs in three steps.

| Loss | Action |
| --- | --- |
| 0.1% | Stop adding, and bring the reUSD borrowed back towards the pool's reUSD share. |
| 0.2% | Cut the position by half. |
| 0.3% | Exit fully. |

If the position is entered at par with all the reUSD borrowed, these losses only arise if reUSD trades above par, at about 1.0024, 1.0044 and 1.0062. Minting at par keeps reUSD from staying far above it. A fall in reUSD is a gain for the position, but a fall below 0.98 for a day, or the pool passing 90% reUSD, would signal distress at Resupply and trigger a full exit. Redemptions against the fund's pair are rebalanced the same day.

## s2.insurance
Resupply's insurance pool holds reUSD deposited by users. It buys the collateral of liquidated borrowers and absorbs bad debt first if a collateral market fails. Beyond its size the protocol carries the loss, and reUSD would weaken. The pool earns 10% of protocol fees plus RSUP, and withdrawals take seven days.

Today it holds {ip_reusd} against {reusd_supply} of reUSD, about {ip_cov} coverage, down from 38.7M before the 2025 exploit, when it absorbed 6M of bad debt. It matters to this position in two ways. A larger pool makes a disorderly reUSD collapse less likely, although this structure gains in a depeg. And if the Curve Lend market holding the fund's crvUSD collateral failed, the pool rather than the market would take the fund's debt and collateral. Coverage is checked daily, and below 3% the position would be reduced.

## s2.reputation
In June 2025 an attacker manipulated the exchange rate of a newly listed, thin market and borrowed about 10M reUSD against almost no collateral. The treasury, partners and the insurance pool covered the bad debt, and the code was changed. The published audit list still shows only the two reviews from January and February 2025. TVL has grown since. This is the weakest part of the case, and the reason the position would stay smaller and on watch.

## s2.rewards_note
Borrow rewards are paid in CRV, RSUP and CVX, all of them liquid. CRV is most of it and can be hedged. The model uses the level the Resupply interface shows today, about 4.2% (CRV about 3.9% and RSUP about 0.6%), and scales the pair's daily reward history to that level, so the shape of the history is kept. The history source records lower absolute levels ({hist_rewards} over the last 30 days). Using it instead would lower the result by about 2 to 3 points.

## s2.found
Found while screening Curve pools with high boosted yield. The reUSD exposure in the pool led to the funding-hedge idea, and Resupply is the natural place to borrow reUSD, paying rewards on top of a borrow cost near 3%.

## s2.audit
The sources are the daily reward and TVL history of the Stake DAO vault and the Curve pool, Resupply's borrow cost and reward history for the pair, Curve Lend's lending rate for the sfrxUSD market, and the reUSD price. The exact structure has existed since 31 July 2026. Before that, the model uses the closest Resupply pair as a stand-in.

## s2.exit
To exit, withdraw from Stake DAO, remove the liquidity (balanced, or in tranches if the pool is heavy in reUSD), repay the reUSD and withdraw the crvUSD. Resupply's communal redemption can also repay part of the debt against the fund's collateral when reUSD trades below par, which shrinks the position.

## s2.ic
From the team I would want a code and forensic review of Resupply, since no audit has been published since the 2025 exploit. The guardian Safe, the upgrade operator and the vault-share price oracle need the most attention. The standard signing and key-management review applies too, and the trading desk would handle CRV sales and hedging.

The yield exists because reUSD has a weak reputation after the exploit and most lenders avoid it. The funding structure turns its main risk, a depeg, into a small gain.

The most likely cause of a loss would be a Resupply incident affecting the collateral side, or CRV emissions to the pool falling while the position stayed in.

## stable.usdsui
USDSUI is issued by Bridge, a Stripe company registered with FinCEN as a money transmitter. Bridge mints and redeems it 1:1 for eligible institutional customers. Reserves are about 90% short-dated Treasury bills and 10% cash, held in segregated accounts at Lead Bank, BlackRock and Fidelity. Supply is about \$77M and growing.

Bridge publishes the reserves through its own real-time feed, but no independent firm attests to them yet. That is the main reason Pharos, an independent rating service, grades USDSUI C- (50/100). Redemption limited to institutional customers and minting controlled by a single key also weigh on the grade. The peg record itself is clean, with no incidents and widest moves of +1.30% and -0.63%. For comparison, USDC is rated A+ (90/100) and is examined monthly by Deloitte.

In this structure the fund owes exactly the USDSUI it holds, so it never needs to redeem or sell USDSUI in size. The weaknesses that matter are a depeg, which the liquidation distance covers, and the single-key mint, which Current Finance's borrow caps limit. Both are covered on the Risk Controls and Stress Tests page. Bridge's package upgrade key is also a single wallet, so an upgrade could in principle freeze the USDSUI the fund holds in vault 2. And Current Finance prices USDSUI from a Pyth feed with a minimum of only two publishers.

## stable.usd1
USD1 is issued 1:1 by BitGo Trust Company under a US national trust charter. Reserves are short-term Treasury bills, government money-market funds and bank deposits, all convertible within a day, with monthly attestations and a real-time proof-of-reserve feed. Supply is about \$4.4B. The issuer can freeze tokens, and redemption runs only through the issuer, which is the weakest part of the design. The peg has held near par for over a year, and USD1 is not authorized under MiCA. In this strategy the fund holds and owes USD1 in equal amounts, so its price does not drive the result.

## stable.reusd
reUSD is a crypto-collateralized stablecoin minted against Curve Lend and Fraxlend deposits of crvUSD and frxUSD, with about 97% of the collateral in crvUSD lending markets. A 1% redemption fee sets a price floor near 0.99. reUSD has traded below par, around 0.989, since 6 August 2026, and has spent most of its history on the weak side of par. Supply is about 50M and growing, and the insurance pool covers about {ip_cov} of it.

A June 2025 exploit left about 9.6M of bad debt, which the treasury, partners and the insurance pool covered. No audit has been published since. The token cannot be frozen and is only minted under on-chain governance. In this strategy the fund both owes and holds reUSD, and a depeg works slightly in its favour, but I would still want reUSD back at par before entering.

## stable.scrvusd
scrvUSD is a savings vault over crvUSD. Holders deposit crvUSD, and the share price rises as Curve directs part of the interest paid by crvUSD borrowers to the vault. It has no privileged mint and no freeze of its own. It does inherit crvUSD's risk, a crypto-collateralized stablecoin whose loans use soft liquidation and whose peg is supported by stabilizer pools. In the Curve pool it is the quarter of the position that is not reUSD, valued through its exchange rate of about 1.108 crvUSD per share.

## screen.intro
I looked for yield that most on-chain desks would miss: structures that need a second step to work, protocols outside the usual lists, and carry that only works at a particular size. I skipped the obvious trades on purpose, such as curated lending on Morpho and Aave, fixed-rate PTs on Pendle and top-tier stablecoins. I assume the team already covers them, and their yield is competed away quickly.

An idea that was not selected is not necessarily a bad one. Each candidate has one of these statuses.

| Status | Meaning |
| --- | --- |
| Rejected | Fails one of the investment tests. |
| Requires automation | Works, but needs hedging or rebalancing infrastructure first. |
| Needs data or monitoring | Promising, but the record is too short or a key fact is missing. |
| Team discussion | Depends on a policy question, such as whether a yield source qualifies. |
| On hold | Fully researched and waiting on stated conditions. |

## screen.repeat
The screen can be repeated every week in four steps.

1. Scan every stablecoin market with a headline yield of 12% or more on the main lending, liquidity and yield venues.
2. Filter automatically on capacity at \$1.5M (free borrow liquidity, pool size, rate curve) and on the source of the income.
3. Review the rest by hand: where the yield comes from, admin keys, oracle, exit path and reward terms.
4. For each one left, check whether a hedge or a two-position structure improves it.

## method.assumptions
| Item | Assumption |
| --- | --- |
| Structure | Two Multiply vaults at the stated leverage, sized so the USDSUI owed equals the USDSUI held. |
| Size effects | The fund's deposits dilute SUI rewards pro rata. Its borrowing moves utilization along the rate curve measured from Current Finance's hourly data. |
| Rewards | Only SUI rewards paid directly on deposits. Points and locked season rewards are excluded. Rewards are claimed daily and sold or hedged the same day. |
| Costs | A 0.01% Multiply fee on the leveraged size and swap costs from live Cetus quotes. A fast-exit provision of 0.028% of equity per unit of leverage, and a stressed exit at 0.2% slippage on every swap. |
| Period | Daily history from 16 April 2026, when rewards start in the data. September conditions are the current base. |

## durability.wlfi
WLFI rewards are paid through weekly Merkl campaigns of about 2.30M WLFI each, which have run without a break since late April. The current one ends on 5 October. The campaigns are funded from one wallet holding about 5.6M WLFI, roughly two and a half weeks of rewards, which is topped up as it goes. I would track each week's renewal and the wallet's balance, and treat a missed renewal as the end of the rewards. The sources are the Merkl campaign page and API, the funding wallet, World Liberty Financial's governance forum and announcements, and Dolomite's channels.

## durability.crv
CRV emissions are set every week by Curve gauge votes. The reUSD/scrvUSD gauge receives about 7.2% of all CRV emissions this week, rising to 7.6% next week. Much of that weight comes from Resupply's own veCRV voting for its pools. I would track the gauge weight each week, along with the vote-incentive markets where protocols pay for votes.

## cur.structure
The position has two vaults, both Multiply positions on Current Finance.

| | Deposits | Borrows | Swaps the loan into |
| --- | --- | --- | --- |
| Vault 1 | USDC | USDSUI | USDC |
| Vault 2 | USDSUI | USDC | USDSUI |

At {L}x, {e1} of the equity goes into vault 1 and {e2} into vault 2. With that split, the USDSUI owed in vault 1 equals the USDSUI held in vault 2. The fund has no net USDSUI, and the position behaves as USDC.

The income is the lending spread on both stablecoins plus the SUI rewards paid on both deposits. Rewards accrue continuously and can be claimed daily. Current Finance's points programme and locked season rewards are not counted.

## cur.yield_note
Rates come from Current Finance's hourly history, and rewards from Current Finance's reward rate for each market. At this size the fund's own deposits dilute the rewards, and its borrowing pushes utilization along the rate curve shown below.

## cur.curve
Both markets follow the same rate curve, measured from Current Finance's hourly data. Borrowing costs about 0.5% plus 5.6% per unit of utilization up to an 80% kink, where the rate is about 5%. Above the kink the rate rises by roughly 0.9 points for every extra 1% of utilization.

USDSUI usually sits near the kink, so its borrow rate is the one to watch. Because the fund lends and borrows the same amount of USDSUI, part of any rise in the borrow rate comes back as higher lending income. Net, the fund carries only about a third of a USDSUI rate spike.

## cur.record
The returns are rebuilt from Current Finance's own data since launch on 23 March 2026: hourly borrow and supply rates, utilization, amounts supplied and borrowed, and prices. The SUI reward rates are Current Finance's own figures. Today's come straight from its reward API, and the daily history is the record DefiLlama keeps of the same figures.

The pools grew about four times between July and September, and that growth is what makes \$1.5M fit today. At this size the strategy would have cleared 12% in May, August and September. In June and July the pools were about a third of today's size, so the yield at \$1.5M would have been lower.

## cur.costs
Costs come from live swap quotes and Current Finance's 0.01% Multiply fee on the leveraged size. Buying USDSUI costs about 0.02% to 0.03%, because it trades slightly above par. Selling it costs close to nothing.

In the fund's accounts I would provision the cost of a fast exit at 0.028% of equity per unit of leverage. I also stress-test the exit at the full 0.2% slippage limit on every swap. Both figures assume every swap is made in full. Repaying one position's debt with the other's proceeds reduces the swaps, so the real cost should be somewhat lower.

## cur.leverage
I set leverage so that a liquidation needs a move many times larger than anything the pair has done. USDSUI's widest moves on record are +1.30% and -0.63%.

Current Finance prices USDSUI and USDC from Pyth and rejects any price more than 5% away from a reference price set by its admin. A faulty or manipulated feed therefore cannot push a vault into liquidation. A real depeg beyond 5% would also stop price-dependent actions until the admin updates the reference, and the governance module lets the admin change those tolerances without a timelock.

At 3.5x a vault is only liquidated by a move of about 16% to 19%, more than ten times the widest on record. At 4.5x the distance falls to about 8.5% to 9%, still about 6.5 times the widest move and outside the 5% band, so 4.5x is the ceiling. I would only move towards it after six to twelve months without problems and with insurance at a price that keeps the yield above the 12% hurdle.

## cur.controls
I checked the controls on-chain through Sui's GraphQL interface, against the five audit reports and against Current Finance's published security material and code interfaces.

| Area | What I found |
| --- | --- |
| Admin capabilities | All admin capabilities sit inside one shared governance object. Parameter changes go through a one-day timelock: proposed, then executed after the delay. The Asymptotic audit found the delay set to a 10-second test value, and it was raised to one day. |
| Immediate actions | Emergency halts, oracle tolerance changes, liquidation-programme cancellations, referral settings and revenue transfers to the treasury act without a timelock. The SuperAdmin role cannot be revoked if compromised, so its key security matters most. |
| Code upgrades | Signed by a 3-of-5 multisig. The last upgrade was on 14 August 2026. The signers are not published, which is a question for the team. |
| Caller capabilities | Two single-key wallets hold caller capabilities. Their permissions cover flash loans, which must be repaid in the same transaction, and opening E-Mode positions, which affects only the holder's own position. The admin can revoke them. |
| Oracles | Pyth, with a minimum of 2 publishers for USDSUI and 3 for USDC. Prices more than 5% away from the admin reference are rejected. Valuations use an average price and alarms use the spot price. |
| Liquidations | Partial, at most 20% of a debt at a time, run by vetted liquidators using flash loans. A Sherlock finding that let liquidators exploit the lag of the average price was fixed. Auto-deleveraging only starts after a delay. |
| Limits | Daily caps on new borrowing and on withdrawals for each asset. An acknowledged Sherlock finding shows they can be kept artificially full. |
| Insurance | Nexus Mutual quoted cover for the position (see below). |

## cur.team
These are the parts where I would rely on the team.

| Area | What I would ask for |
| --- | --- |
| Smart contracts | A review of the Multiply router, the caller capabilities and the governance functions that act without a timelock. |
| Keys and signing | A separate wallet setup per vault, simulation and decoding of every transaction before signing, protection against spoofed addresses, and no blind signing. |
| Governance | Who holds the SuperAdmin and parameter roles, how those keys are secured, and the multisig signers. |
| Oracles | How the USDSUI feed, with only two publishers, and the admin reference price behave in a depeg, before any step above 3.5x. |
| Trading | Daily SUI sales, and the build and exit in tranches. |

## cur.why
Most active curators and allocators work on EVM networks and Solana. Sui is not EVM-compatible. Their integrations, tooling and infrastructure do not carry over and have to be built from scratch, and few desks have done that.

Current Finance launched in March 2026. It is not yet on most approved lists, or it is still in an observation period.

The structure also takes work, since the yield needs two linked vaults built in tranches rather than a single deposit. Capacity is limited too. The pools have grown quickly, but a much larger allocation would dilute the rewards.

## cur.premortem
The most likely way this loses money is a protocol exploit at Current Finance that pauses withdrawals before the position can be unwound.

The second is a cut in SUI rewards. Without rewards the lending spread is negative, so staying in too long would turn the carry into a loss.

A modest position keeps both risks small, together with monitoring of Current Finance's admin actions, a daily check of the reward rate, an exit sized to the market, and insurance if it can be bought at a sensible price.

## s1.hold
This strategy is fully researched and could be funded, but I am holding it back for three reasons. The yield rests on WLFI rewards with no published budget, paid in weekly campaigns from one wallet that holds about two and a half weeks of rewards. Most of the USD1 borrowed on Dolomite is backed by WLFI, which liquidators could not sell at size. And Dolomite is administered by a 2-of-3 multisig with a 5-minute delay. I would reconsider it if a multi-month reward budget were confirmed and either the WLFI-backed share of USD1 debt or Dolomite's admin setup improved.

## s2.hold
reUSD has traded below par since early August and printed as low as 0.82 in April. Holding liquidity in its pool means taking on more reUSD as it falls, and Resupply has published no audit since its 2025 exploit. I would reconsider the strategy once reUSD holds par for a sustained period and the code changes have been reviewed independently.

## summary.hold_box
Two more strategies were fully researched and are on hold until specific conditions are met: a [USD1 carry on Dolomite](usd1) and a [reUSD liquidity position on Curve](reusd). Each has its own page at the end of the report.

## cur.partners
Current Finance's contracts were audited by Asymptotic (lending, leverage and governance), MoveBit (protocol and oracle in September 2025, governance earlier), ScaleBit (a penetration test) and Zellic, and went through a public Sherlock contest in March 2026. Asymptotic also verified the contracts formally at launch, using the Sui Prover it built for this work, and it has reviewed every code change since.

| Review | Findings | Status |
| --- | --- | --- |
| MoveBit, protocol and oracle (Sep 2025) | 1 critical, 4 major, 3 medium, 6 minor or informational | Critical fixed. Two major findings acknowledged as design choices: self-liquidation, now removed by separate borrowing and liquidation thresholds, and a strict price-freshness rule that requires a price update in the same transaction. |
| Asymptotic, lending | 1 high, 4 medium, plus low and advisory | All remediated |
| Asymptotic, leverage and governance | 4 medium, 9 low, 6 advisory | All remediated, including the timelock raised from 10 seconds to one day |
| MoveBit, governance | 2 medium, 2 informational | One medium fixed, one acknowledged |
| Sherlock contest (Mar 2026) | 2 high, 4 medium, 4 low | All fixed or acknowledged. One acknowledged medium lets an attacker keep the daily caps full. |

Allez Labs reviews every listing, cap and parameter change. It was founded by Aave's founding risk manager and also works on risk for Aave and Kamino. Hypernative monitors the protocol in real time, Pyth supplies the prices, and Nexus Mutual sells cover.

Formal verification proves that the contracts do what their specification says. It does not cover the Sui chain itself, admin decisions or oracle inputs, which is why the other controls still matter.

## cur.sui
Rewards accrue continuously and can be claimed every day. I would claim daily and either sell the SUI or hedge it with a short perpetual the same day. The exposure is then never more than one day of rewards, under \$800 at \$1.5M. Once the monitoring tooling is built, claims and hedges can run automatically, together with responses to stress alerts.

## method.sources
Every figure the result depends on comes from Current Finance itself. DefiLlama is used only as a record of past reward rates, which it copies once a day from Current Finance's own API.

| Source | What it provides |
| --- | --- |
| Current Finance chart API | Hourly history since launch: borrow and supply rates, utilization, amounts supplied and borrowed, and prices |
| Current Finance market API | Live rates, supply, borrow, caps and LTVs for each market |
| Current Finance reward API | Live SUI reward rates for each market, the same figures the app shows |
| Current Finance reserve pages and documentation | Daily borrowing and withdrawal limits, E-Mode settings, security material |
| Sui GraphQL | Package, upgrade and capability objects, and multisig signatures |
| Cetus | Live USDSUI / USDC swap quotes |
| Pharos (pharos.watch) | Independent ratings for USDC and USDSUI: reserves, assurance, controls, peg history and early-warning score |
| DefiLlama | Daily record of Current Finance's past SUI reward rates, used for the reward history only |
| CoinGecko | SUI order-book depth and derivatives open interest |
| Hyperliquid info API | Daily SUI prices for the reward-exposure measures |
| CertiK Skynet | Protocol security score |

## s1.controls
I checked every contract in the strategy on-chain on 30 September.

| Area | What I found |
| --- | --- |
| Dolomite admin | The weakest point. A 2-of-3 Safe runs the protocol through a 5-minute timelock, and the pause and excess-token roles bypass it. That is thin for a protocol holding over \$400M. |
| USD1 mint and freeze | The admin is a 3-of-6 Safe with a 3-day delay, but one minter and one freezer are single wallets. A compromised minter could create unbacked USD1, post it on Dolomite at about \$1 and borrow the USDC the fund supplies, the same pattern as the Resolv exploit in March 2026. |
| Oracles | Chainlink's USD1, USDC and WLFI feeds. Dolomite accepts prices up to 36 hours old, and its owner can swap feeds. |
| Rewards | Paid through Merkl, governed by a 4-of-6 Safe, with a one-hour dispute window on each payout. |

## s2.controls
I checked every contract in the strategy on-chain on 30 September.

| Area | What I found |
| --- | --- |
| Resupply governance | On-chain votes with a 7-day voting period and a 1-day delay. A 3-of-5 guardian Safe can pause pairs and insurance-pool withdrawals, and the same Safe manages an upgrade operator whose scope needs review. |
| Collateral pricing | The fund's collateral is priced from the lending vault's share price, the same type of oracle exploited in June 2025. |
| Stake DAO and Curve | Well controlled. The vault has a 5-day timelock, and the pool's code cannot be upgraded. |

## s1.overview
The strategy lends USDC and USD1 on Dolomite through two linked positions. The first uses USDC as collateral to borrow USD1. The second uses that USD1 as collateral to borrow USDC. The USD1 owed equals the USD1 held. The income is Dolomite's lending spread plus WLFI rewards paid weekly through Merkl. At 3x it earned {usd1_window} a year since the rewards began, above 12% every month, with room for \$1.5M.

## cur.controls_intro
This page maps every risk in the EEA DeFi risk list, the TradFi credit additions and the ESMA suitability guidelines to this position. For each one it shows how the risk applies, what covers it, where the data comes from and when to act. Checks K1 to K9 run in the console on the Monitoring and Operations page. The stress tests use September conditions at the fund's size.

## summary.take
The case for it is straightforward. The fund's money stays in USDC, it has no net exposure to USDSUI's price, and the SUI rewards are easy to sell every day. Current Finance's code has been reviewed by five independent security firms and in a public bug-finding contest, and an outside risk firm, Allez Labs, reviews its settings.

There are three weaknesses. Current Finance is only six months old. Without the SUI rewards the position would lose about 4% a year, so the return depends on Current Finance continuing to pay them. And USDSUI's issuer, Bridge, a regulated Stripe company, reports its own reserves, but no independent firm has checked them yet.

I would review the position if either stablecoin moved more than 0.5% away from one dollar. I would exit if it moved more than 2%, if Current Finance were hacked or its administrators made an unexplained change, or if the return stayed below 12% for two weeks.

## s1.method
The data comes from Dolomite's Ethereum subgraph (Goldsky) and DolomiteMargin contract reads (Ethereum RPC, Blockscout) for rates, positions and controls. Merkl provides the WLFI reward campaigns, the Hyperliquid info API and CoinGecko provide WLFI prices, depth and open interest, and Pharos provides USD1's rating.

The model keeps both positions at equal health and assumes liquidation at 90% of collateral value. WLFI rewards are counted at the daily reward rate. Gas and the cost of selling rewards are not deducted, as they are small at this size.

## s2.method
The data comes from the Curve and Stake DAO APIs for the pool and the vault, the Resupply pair data (hippo.army API) and Resupply contract reads for borrow costs, rewards, the insurance pool and controls, DefiLlama for pool history, Beefy for the autocompounding comparison, and Pharos for the ratings of reUSD and scrvUSD.

The model assumes the pool is about 77% reUSD, takes borrow rewards from the pair's history (lower than the interface shows), and dilutes CRV rewards by the fund's size against the pool.

## scope.intro
Each question in the case study brief, with a short answer and a link to the page that covers it.

## scope.01
Every candidate went through the same investment tests ({n_screened} in total). This strategy came from searching lending platforms on newer blockchains for rewards paid on both sides of a stablecoin pair. The search can be repeated every week from the same data sources.

## scope.02
Returns are rebuilt from Current Finance's own published data since launch: hourly interest rates, how much is deposited and how much is lent out, and its SUI reward rates. At \$1.5M and 3.5 times leverage the position earned {aug} in August and {sep} in September. The scripts and data are in the repository, and a small live test confirmed that the positions and reward payouts work as described.

## scope.03
Entry in batches of \$150,000 to \$300,000 over three to four days. To exit, each position is partly closed and the proceeds repay the other position's debt, which reduces the amount swapped. The swaps run in batches of up to \$1M. A full exit takes about two days. Entry costs about {entry}. Exit costs are set aside at {exit_prov} and tested at {exit_stress}. A hack that freezes withdrawals is outside this plan.

## scope.04
At 3.5 times leverage and \$1.5M, over the last 30 days: interest earned {lend}, SUI rewards {rew}, interest paid {borrow}, return {net}. Leverage adds to the return because the deposits, including rewards, earn more than the loans cost.

## scope.05
The main risks are ranked in this summary and covered in detail on the risk pages. A table of 57 controls checks the position against three standard risk lists: the Enterprise Ethereum Alliance's list of DeFi risks, traditional credit risks, and the EU's ESMA guidelines. Stress tests cover reward cuts, jumps in interest rates, a stablecoin losing its dollar value, price-feed failures and USDSUI created without backing.

## scope.06
Nine alarms (K1 to K9), each with a warning level and an action level, shown on a monitoring screen with live data. They use Current Finance's own data, events recorded on the Sui blockchain, an independent stablecoin rating service (Pharos) and a security monitoring firm (Hypernative).

## scope.07
A review of the code that builds the leveraged positions and of the administrators' powers, secure handling of the fund's keys and transactions, a review of the USDSUI price feed before any increase above 3.5 times, and the trading desk for the daily SUI sales and the batches in and out.

## scope.08
Most curators and allocators work on EVM networks and Solana, and Sui is not EVM-compatible, so their tooling has to be rebuilt from scratch. Current Finance only launched in March 2026. The position needs two linked parts, and the room is limited: Current Finance's pools only became large enough for this size in August.

## scope.09
Most likely, a hack of Current Finance that froze withdrawals before the fund could get out. Second, a cut in the SUI rewards followed by a late exit, since without the rewards the position loses money.

## cur.two_vaults
One position on its own would leave the fund owing USDSUI while holding USDC, so a rise in USDSUI's price would cost the fund money. The second position holds the same amount of USDSUI that the first one owes, which cancels that exposure. It also lets the fund earn the SUI rewards paid on USDSUI deposits as well as those on USDC.

Building the position means swapping about \$2.2M between USDC and USDSUI. That is done in batches, so each swap is small enough not to move the price, and the swaps in the two positions run in opposite directions and partly offset each other. USDSUI's share of the pool that is lent out rises by only about two points.

Current Finance only lets an account lend or borrow a given coin in one direction, so the two directions sit in separate positions. A small pilot confirmed that both can be held at the same time and that SUI rewards arrive and can be withdrawn.

## cur.build
I would build it as fast as the market allows without moving the price. Tranches of \$150k to \$300k a side alternate between the two vaults, so each vault's swap partly offsets the other's. The next tranche goes in only when USDSUI is back at par and the quoted slippage is within limits.

The real limit is Current Finance's cap on new USDSUI borrowing, \$0.7M a day across all users. That puts the full build at about three to four days.

Entry costs can be cut further. USDC can arrive on Sui directly from an exchange that supports Sui withdrawals or through a bridge, and with an account at Bridge the fund can create USDSUI one to one instead of buying it on the market.

## cur.exit
A Multiply position cannot borrow or withdraw on its own. It can be partly closed, which swaps part of the collateral to repay part of the debt and returns the rest in USDC or USDSUI, and its debt can be repaid with coins from outside. The pilot vaults confirmed both.

The exit alternates between the two positions. Part of vault 1 is closed into USDC, which repays part of vault 2's USDC debt. Part of vault 2 is then closed into USDSUI, which repays part of vault 1's USDSUI debt, and so on. Each repayment from outside means less has to be swapped inside the next close, so the exit is cheaper than closing each position on its own. It is not free: every partial close still swaps part of the collateral.

Each close also withdraws collateral, so it needs free cash in the lending pools. Today the USDSUI pool has about \$5.8M free against the \$2.2M the fund would withdraw. In a run on Current Finance that cash can disappear, and the exit then waits for borrowers to repay. The daily withdrawal caps (\$1.3M of USDSUI and \$5M of USDC) are shared by all users, so a full exit takes about two days, and longer if others are leaving at the same time.

## cur.exit_capacity
Today about \$1M of USDSUI can be swapped for less than 0.03%, out of roughly \$8M of pool liquidity on Bluefin, Cetus and Turbos. Bridge mints and redeems USDSUI 1:1, which pulls the price back to par between tranches. I size the position so the whole exit fits in a few of these tranches. Trigger K9 checks the quoted cost of a \$1M swap every day. If that cost rises, the position shrinks until the exit fits again.

## cur.exit_limits
A depeg is unlikely, since Bridge issues and redeems at par. The plan has three limits. First, a protocol exploit that pauses withdrawals: the exit then depends on the protocol rather than on market liquidity, which is the main reason the position stays small. Second, a run that drains free cash from the two lending pools: the exit waits for repayments, which rising rates speed up. Third, the shared daily caps can be deliberately kept full. The Sherlock contest found that an attacker can time withdrawals across the caps' rolling windows to keep them artificially exhausted, and the team acknowledged the finding without a fix. That could stretch the exit by several days.

## cur.matrix_legend
Each control has one of three statuses. In place means a trigger in the monitoring console, a stress test or a step in the plan already covers it. Partly in place means part of it is covered, for example the stablecoin price is watched but not yet the number of oracle publishers. To build means the data or tooling still has to be set up. The priority says when: P1 before funding, P2 within the first month, and P3 once the monitoring infrastructure is in place.

## cur.controls_note
Checked on-chain through Sui GraphQL, against the five audit reports and against Current Finance's published security material and code interfaces, 2 October 2026.

## cur.triggers_note
At the warning level I investigate and prepare the exit. At the action level I act without waiting for a meeting.

## cur.console_note
This is a mock-up. Each check runs on the latest data shown above, and in production the same checks would run on live data every few minutes.

## cur.runbook
1. On a warning, confirm the data, find the cause and prepare the exit transactions.
2. If price or vault health reaches an action level (K1, K2), repay debt in the affected vault or cut both vaults to 2.5x.
3. If utilization, caps, exit capacity or an admin event reach an action level (K3, K6, K9), stop adding and start the exit in tranches.
4. If the net yield stays below 12% (K4, K8), unwind over a few days and rotate.
5. Every day, claim the SUI rewards and sell them or hedge them with a short perpetual.
6. Every month, rebalance both vaults back to 3.5x, since interest on the USDSUI debt slowly lowers vault 1's health.
7. Log each event with the trigger, time, size, cost and outcome.

## cur.price_note
USDSUI's widest recorded moves are +1.30% and -0.63%. On Current Finance's own price feed since April, USDSUI/USDC has stayed between 0.9999 and 1.0024 hourly. The largest one-hour move was 0.085% and the largest one-day move 0.2%.

## cur.sui_liquidity
SUI trades in deep markets, with about \$48M of bids within 2% of the price, \$1.1B of daily spot volume and \$1.4B of perpetual open interest.

## cur.riskmap_note
Trigger IDs refer to the Monitoring and Operations page.

## summary.returns_note
In June and July Current Finance's pools were about a third of today's size, so a \$1.5M position would have diluted the rewards more and earned less.

## screen.date
Search carried out from 28 to 30 September 2026.

## screen.income_test
The income-source test asks where the yield ultimately comes from. It passes for on-chain lending spreads, funding, trading fees and carry, and for stablecoins backed by T-bills or by a transparent on-chain book. It fails for off-chain loans, listed equities or preferreds, reinsurance, CLOs and CeFi arbitrage.

## screen.pipeline_note
These are not proposed today, but they are not dismissed either. Each needs automation, more data or a team decision first.

## screen.open_item
Open item: the scan script and its scheduled output.

## method.files_note
The query scripts write CSV files to the data folder, and the pages only read them.

## method.freshness
Live figures come from Current Finance's API and change each time the data is refreshed. Pinned figures, such as swap quotes, issuer ratings and the on-chain control checks, were taken between 29 September and 2 October 2026 and do not change between runs.

## method.ai_use
I designed and directed the work: the strategy, the risk framework, what to test and how, the structure of the report and every decision in it. AI tools carried out the execution under my direction.

| Area | What I did | What the AI tools did |
| --- | --- | --- |
| Framework | Compiled the risk checklist and the process document, choosing the sources and the structure | Formatting |
| Screening | Chose where to look and which candidates to test, and made every call | Pulled protocol and market data and ran the checks I specified |
| Strategy and backtests | Designed the strategy (two-position structure, leverage policy, entry and exit), set the assumptions and the tests, and interpreted the results | Wrote the code for the data pulls and backtests I specified |
| Dashboard | Set the structure, what to show and the standard for review | Built the pages from my templates |
| Writing | Set the argument and the tone, and edited throughout | Drafted text for my review |

## alloc.intro
Interactive. Rates and positions from Current Finance data to {data_date}. Fund NAV \$35M.

## cur.insurance
Nexus Mutual quoted cover of \$1.4M for about \$5,059 a month, about 4.3% of the cover amount a year, or 4.0% of the fund's equity. It covers smart contract exploits, oracle failure or manipulation, liquidation failure and governance takeover. It excludes depegs, private key breaches and front-end attacks, carries a 5% deductible (\$70,000), and pays only after a 14-day wait, through a claims assessment by the mutual's members rather than under an insurance contract.

| Leverage | Net after costs | After cover at the quoted price | Liquidation distance |
| --- | --- | --- | --- |
| 3.5x | 14.7% | 10.7% | +19% / -16% |
| 4.0x | 15.7% | 11.7% | +13% / -12% |
| 4.5x | 16.7% | 12.7% | +9% / -8.5% |

At the quoted price, only 4.5x clears the hurdle with cover, by 0.7 points, and a reward cut of about 3% would take it below 12%. The cover protects against the largest risk, a protocol exploit, but not against the main extra risk of higher leverage, which is liquidation in a real depeg. An unbacked USDSUI mint from a stolen Bridge key would probably fall under the key-breach exclusion, which is worth confirming. At about 2.2% a year, insured 4.5x would earn the same as uninsured 3.5x. That is the price I would negotiate towards before considering it.

## cur.custody
Each vault is controlled by its owner capability object, and every action on a Multiply position, including claiming rewards, requires that object. Sui has no equivalent of the Safe Roles Modifier for scoping what a signer may do. I would hold both owner capabilities in a Sui multisig, build every transaction through the SDK rather than the web app, and simulate it before signing. Daily claims then need the multisig as well, so claims could move to weekly until automation is in place, at a cost of a few thousand dollars of unhedged SUI.
