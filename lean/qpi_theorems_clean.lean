-- qpi_theorems_clean.lean
-- Lean 4 formalization skeleton for QPI midpoint equivalence.
--
-- IMPORTANT:
-- - This file intentionally does NOT assert infinitude of twin primes.
-- - Any infinitude statement must remain a Conjecture until proven without axioms.

import Mathlib.Data.Nat.Prime
import Mathlib.Data.Nat.Digits

namespace QPI

/-- lastDigit n = n mod 10 -/
def lastDigit (n : ℕ) : ℕ := n % 10

/-- Yellow cell predicate: multiple of 3, ends in 0,2,8 -/
def isYellow (n : ℕ) : Prop :=
  n % 3 = 0 ∧ (lastDigit n = 0 ∨ lastDigit n = 2 ∨ lastDigit n = 8)

/-- Red cell predicate: yellow with both neighbors prime -/
def isRed (n : ℕ) : Prop :=
  isYellow n ∧ Nat.Prime (n - 1) ∧ Nat.Prime (n + 1)

/-- Twin prime pair -/
def isTwinPrime (p : ℕ) : Prop :=
  Nat.Prime p ∧ Nat.Prime (p + 2)

/--
Twin Prime Midpoint Law (correct statement):

For p > 5:
  (p and p+2 prime) ↔ (m=p+1 is a Red cell)

This is an equivalence of definitions + elementary modular facts.
-/
theorem twin_midpoint_equivalence (p : ℕ) (hp : p > 5) :
  isTwinPrime p ↔ isRed (p + 1) := by
  constructor
  · intro h
    rcases h with ⟨hpprime, hp2prime⟩
    -- TODO: prove (p+1) is divisible by 3 because one of {p,p+1,p+2} is divisible by 3
    -- and p,p+2 are primes > 3.
    have hDiv3 : (p + 1) % 3 = 0 := by
      sorry
    -- TODO: prove lastDigit ∈ {0,2,8} for p>5 and p,p+2 prime.
    have hLast : (lastDigit (p + 1) = 0 ∨ lastDigit (p + 1) = 2 ∨ lastDigit (p + 1) = 8) := by
      sorry
    refine ⟨⟨hDiv3, hLast⟩, ?_, ?_⟩
    · -- neighbor (p) prime
      simpa [Nat.add_sub_cancel] using hpprime
    · -- neighbor (p+2) prime
      simpa [Nat.add_assoc] using hp2prime
  · intro hr
    rcases hr with ⟨_, hpprime, hp2prime⟩
    exact ⟨hpprime, by simpa [Nat.add_assoc] using hp2prime⟩

/-- Yellow cells exist beyond any bound (finite constructive existence). -/
lemma yellow_exists_beyond (N : ℕ) : ∃ m > N, isYellow m := by
  -- Example witness: take m = 30*(N+1) which ends in 0 and is divisible by 3.
  refine ⟨30*(N+1), ?_, ?_⟩
  · nlinarith
  · constructor
    · -- divisible by 3
      simp
    · -- last digit is 0
      left
      -- lastDigit (30*(N+1)) = 0 since divisible by 10
      simp [lastDigit]

/-- Conjecture: infinitely many twin primes (external to QPI; not proven here). -/
conjecture twin_prime_infinity : ∀ N : ℕ, ∃ p > N, isTwinPrime p

end QPI
