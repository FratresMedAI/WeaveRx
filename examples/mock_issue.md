# Sample issue for mock triage demos

**Title:** Unable to reproduce nnU-Net training results on BraTS subset

**Body:**

Hi maintainers,

I'm trying to reproduce the BraTS segmentation benchmark using nnU-Net v2
with CUDA 12.1 and PyTorch 2.2. My Dice scores are ~5% lower than reported.

**Environment:** Ubuntu 22.04, MONAI 1.3, single A100
**Config:** default nnUNetTrainer, fold 0

Has anyone seen similar variance? Happy to share my preprocessing logs.
