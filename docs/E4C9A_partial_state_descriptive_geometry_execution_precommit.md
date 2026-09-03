# E4C9A — partial-state descriptive geometry execution

E4C9A executes only the point-estimate geometry frozen in E4C9.

After this precommit, the frozen 40-row E4C6E partial point registry may be opened. The 8 age×tenure points are reconstructed in the five frozen coordinate axes. Every one of the 28 unordered cell pairs is evaluated in the exact pair order frozen by E4C9.

For each pair, E4C9A records the exact five-coordinate difference vector `cell_b - cell_a`.

It then computes exact squared metric distance under both frozen E4C7 metrics:

- M1: d² = ΔH² + ΔK² + ΔD² + ΔI1² + ΔI2².
- M2: d² = ΔH² + ΔK² + ΔD² + 1/2 ΔI1² + 1/2 ΔI2².

The primitive remains squared distance. Square roots are not computed because they generally leave rational arithmetic and are not required by E4C9.

The execution also records each coordinate's exact weighted squared contribution, solely as an algebraic decomposition of the already-frozen metric formula. No contribution share, ranking, threshold, or outcome-based selection is authorized.

Rows remain in frozen pair order. Distances are not sorted and no "largest", "smallest", or best-looking pair is selected during execution.

`se_state` is not used. E4C9A performs no standard error, confidence interval, significance test, PCA, whitening, SVD/eigenvalue dimension test, affine-rank claim, real-inflation estimate, or final scalar.

A pass authorizes a separate descriptive closeout preflight. It does not itself authorize inferential geometry.
