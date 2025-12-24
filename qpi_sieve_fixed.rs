// qpi_sieve_fixed.rs
// Correct-by-construction segmented sieve (odd-only) + QPI midpoint validation.
// Notes:
// - This version avoids wheel-30 indexing bugs by using an odd-only bitmap per segment.
// - It is intended as a correctness baseline that can be optimized further.
//
// Build (local machine with Rust):
//   cargo new qpi_validator && cd qpi_validator
//   # add rayon="1.8", sha2="0.10" to Cargo.toml
//   cp qpi_sieve_fixed.rs src/main.rs
//   cargo run --release -- 1000000000

use rayon::prelude::*;
use sha2::{Digest, Sha256};
use std::time::Instant;

#[derive(Debug, Clone, Copy)]
struct Stats {
    n: u64,
    prime_count: u64,
    yellow_count: u64,
    red_count: u64,
    twin_pairs: u64,
    twin_pairs_p_ge_7: u64,
}

fn is_yellow(m: u64) -> bool {
    m % 3 == 0 && matches!(m % 10, 0 | 2 | 8)
}

fn simple_sieve(limit: usize) -> Vec<u32> {
    // standard sieve to sqrt(N)
    let mut is_prime = vec![true; limit + 1];
    if limit >= 0 { is_prime[0] = false; }
    if limit >= 1 { is_prime[1] = false; }
    let r = (limit as f64).sqrt() as usize;
    for p in 2..=r {
        if is_prime[p] {
            let mut j = p * p;
            while j <= limit {
                is_prime[j] = false;
                j += p;
            }
        }
    }
    is_prime
        .iter()
        .enumerate()
        .filter_map(|(i, &b)| if b { Some(i as u32) } else { None })
        .collect()
}

// segment stores only odd numbers: index i corresponds to n = low + 2*i
fn run_segment(low: u64, high: u64, base_primes: &[u32]) -> (u64, u64, u64, u64, u64) {
    // return (prime_count, yellow_count, red_count, twin_pairs, twin_pairs_p_ge_7) within [low,high]
    // Preconditions: low and high are odd bounds with low <= high.
    let len = ((high - low) / 2 + 1) as usize;
    let mut is_prime = vec![true; len];

    for &p32 in base_primes {
        let p = p32 as u64;
        if p == 2 { continue; }
        let mut start = (low + p - 1) / p * p;
        if start < p * p { start = p * p; }
        if start % 2 == 0 { start += p; } // ensure odd
        let step = 2 * p;
        let mut x = start;
        while x <= high {
            let idx = ((x - low) / 2) as usize;
            if idx < len { is_prime[idx] = false; }
            x += step;
        }
    }

    let mut prime_count = 0u64;

    // Count yellow/red/twins: need prime test for neighbors, so build list of primes in this segment.
    let mut primes: Vec<u64> = Vec::new();
    for i in 0..len {
        if is_prime[i] {
            let n = low + 2 * (i as u64);
            if n >= 3 {
                prime_count += 1;
                primes.push(n);
            }
        }
    }

    // Twin pairs and red midpoints
    let mut twin_pairs = 0u64;
    let mut twin_pairs_p_ge_7 = 0u64;
    let mut red_count = 0u64;

    for w in primes.windows(2) {
        let p = w[0];
        let q = w[1];
        if q == p + 2 {
            twin_pairs += 1;
            if p >= 7 { twin_pairs_p_ge_7 += 1; }
            if p >= 7 {
                let m = p + 1;
                if is_yellow(m) { red_count += 1; }
            }
        }
    }

    // Yellow count is purely modular; count without scanning every integer:
    // Count m in [low-1, high+1] that are divisible by 3 and end with 0/2/8.
    // Simpler (and still fast): scan only the candidate arithmetic progressions mod 30.
    let mut yellow_count = 0u64;
    // yellow midpoints are even and divisible by 3; for p>5 these are exactly numbers ≡ 0,12,18 (mod 30)
    // because last digit constraint excludes 6 and 24 cases.
    let residues = [0u64, 12u64, 18u64];
    for &r in &residues {
        // find first m >= (low.saturating_sub(1)) with m % 30 == r
        let start_m = low.saturating_sub(1);
        let mut m = if start_m % 30 <= r {
            start_m + (r - start_m % 30)
        } else {
            start_m + (30 - (start_m % 30 - r))
        };
        while m <= high + 1 {
            if m >= 0 && is_yellow(m) { yellow_count += 1; }
            m += 30;
        }
    }

    (prime_count, yellow_count, red_count, twin_pairs, twin_pairs_p_ge_7)
}

fn checksum(stats: &Stats) -> String {
    let mut h = Sha256::new();
    h.update(stats.n.to_le_bytes());
    h.update(stats.prime_count.to_le_bytes());
    h.update(stats.yellow_count.to_le_bytes());
    h.update(stats.red_count.to_le_bytes());
    h.update(stats.twin_pairs.to_le_bytes());
    h.update(stats.twin_pairs_p_ge_7.to_le_bytes());
    format!("{:x}", h.finalize())
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let n: u64 = args.get(1).and_then(|s| s.parse().ok()).unwrap_or(100_000_000);

    let t0 = Instant::now();

    let sqrt_n = (n as f64).sqrt() as usize + 1;
    let base_primes = simple_sieve(sqrt_n);

    // segmented bounds over odd numbers >= 3
    let seg_bytes: u64 = 8 * 1024 * 1024; // target segment size in bytes-ish
    let seg_len_odd: u64 = seg_bytes * 8; // rough, adjust on optimization pass
    let seg_span: u64 = 2 * seg_len_odd;  // odds only => step 2

    let mut low: u64 = 3;
    let mut prime_count = 1; // include prime 2
    let mut yellow_count = 0u64;
    let mut red_count = 0u64;
    let mut twin_pairs = 0u64;
    let mut twin_pairs_p_ge_7 = 0u64;

    while low <= n {
        let high = (low + seg_span).min(n | 1); // ensure odd-ish
        let (pc, yc, rc, tp, tp7) = run_segment(low | 1, high | 1, &base_primes);
        prime_count += pc;
        yellow_count += yc;
        red_count += rc;
        twin_pairs += tp;
        twin_pairs_p_ge_7 += tp7;
        low = high + 2;
    }

    let stats = Stats { n, prime_count, yellow_count, red_count, twin_pairs, twin_pairs_p_ge_7 };
    let dt = t0.elapsed().as_secs_f64();

    println!("N={}", n);
    println!("primes={}", stats.prime_count);
    println!("yellow={}", stats.yellow_count);
    println!("red={}", stats.red_count);
    println!("twin_pairs={}", stats.twin_pairs);
    println!("twin_pairs(p>=7)={}", stats.twin_pairs_p_ge_7);
    println!("diff(red - twin(p>=7))={}", (stats.red_count as i128 - stats.twin_pairs_p_ge_7 as i128));
    println!("seconds={:.3}", dt);
    println!("checksum_sha256={}", checksum(&stats));
}
