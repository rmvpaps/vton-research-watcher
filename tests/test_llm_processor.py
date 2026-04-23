import pytest
import respx
import httpx

from processor import HostedLLMProcessor
from shared import Article,settings 

@pytest.mark.asyncio
async def test_evaluate_score_good_match():
        keywords = [
        "3D Reconstruction",
        "Photogrammetry",
        "Human Parametric Model",
        "Virtual Try On",
        "SMPL",
        "Anny"
        ]
        art1 = Article(arxiv_id="2001.2001",
                       title="ETCH-X: Robustify Expressive Body Fitting to Clothed Humans with Composable Datasets",
                       abstract="Human body fitting, which aligns parametric body models such as SMPL to raw 3D point clouds of clothed humans, serves as a crucial first step for downstream tasks like animation and texturing. An effective fitting method should be both locally expressive-capturing fine details such as hands and facial features-and globally robust to handle real-world challenges, including clothing dynamics, pose variations, and noisy or partial inputs. Existing approaches typically excel in only one aspect, lacking an all-in-one solution. We upgrade ETCH to ETCH-X, which leverages a tightness-aware fitting paradigm to filter out clothing dynamics (\"undress\"), extends expressiveness with SMPL-X, and replaces explicit sparse markers (which are highly sensitive to partial data) with implicit dense correspondences (\"dense fit\") for more robust and fine-grained body fitting. Our disentangled \"undress\" and \"dense fit\" modular stages enable separate and scalable training on composable data sources, including diverse simulated garments (CLOTH3D), large-scale full-body motions (AMASS), and fine-grained hand gestures (InterHand2.6M), improving outfit generalization and pose robustness of both bodies and hands. Our approach achieves robust and expressive fitting across diverse clothing, poses, and levels of input completeness, delivering a substantial performance improvement over ETCH on both: 1) seen data, such as 4D-Dress (MPJPE-All, 33.0% ) and CAPE (V2V-Hands, 35.8% ), and 2) unseen data, such as BEDLAM2.0 (MPJPE-All, 80.8% ; V2V-All, 80.5% )."
                       
                       )
        processor = HostedLLMProcessor(keywords=keywords,api_key=settings.llm_api_key,provider_url=settings.llm_host)
        score = await processor.evaluate_abstract(art1)

        assert score is not None
        assert score.score >= 0 and score.score <= 1
        assert score.score > 0.8

        
# @pytest.mark.asyncio
# async def test_evaluate_score_no_match():
#         keywords = [
#         "3D Reconstruction",
#         "Photogrammetry",
#         "Human Parametric Model",
#         "Virtual Try On"
#         ]
#         art1 = Article(arxiv_id="2001.2001",
#                        title="Measuring neutrino mass and asymmetry through galaxy pairwise peculiar velocity",
#                        abstract="Cosmic neutrinos are among the most abundant fermions in the Universe, yet the values of their masses and chemical potentials remain uncertain. In this Letter, we present the first constraints on the total neutrino mass M_\nu and the neutrino asymmetry parameter \eta^2 derived from the mean galaxy pairwise peculiar velocity in the quasi-linear and nonlinear regimes. We develop a simulation-based analysis pipeline that connects neutrino properties to predictions of galaxy pairwise velocity, and apply it to galaxy data from the Cosmicflows-4 grouped catalog. Our analysis is performed within two independent cosmological frameworks, based on cosmological parameters derived from Cosmic microwave background (CMB) and local distance ladder measurements, respectively. By performing fits to the galaxy pairwise velocity, we obtain consistent constraints from both frameworks. Quoting posterior means with 68% CL, we find M_\nu = 0.24^{+0.34}_{-0.18}\ \mathrm{eV} and \eta^2 = 2.14^{+0.30}_{-0.32} in the CMB framework, and M_\nu = 0.37^{+0.34}_{-0.26}\ \mathrm{eV} and \eta^2 = 2.4^{+2.1}_{-1.6} in the local framework. In particular, we find a 7\sigma measurement of a non-zero neutrino asymmetry in the CMB framework. These neutrino parameters are consistent with those, in our previous work, obtained from the Planck CMB temperature power spectrum. These results demonstrate that galaxy pairwise velocities provide an independent and sensitive probe of neutrino properties, opening a new avenue for testing neutrino physics with large-scale structure observations"
#                        )
#         processor = HostedLLMProcessor(keywords=keywords,api_key=settings.llm_api_key,provider_url=settings.llm_host)
#         score = await processor.evaluate_abstract(art1)

#         assert score is not None
#         assert score.score >= 0 and score.score <= 1
#         assert score.score < 0.5


# @pytest.mark.asyncio
# async def test_evaluate_score_partial_match():
#         keywords = [
#         "3D Reconstruction",
#         "Photogrammetry",
#         "Human Parametric Model",
#         "Virtual Try On"
#         ]
#         art1 = Article(arxiv_id="2001.2001",
#                        title="Fixing 3D Reconstructions via Multi-View Synchronization",
#                        abstract="We present SyncFix, a framework that enforces cross-view consistency during the diffusion-based refinement of reconstructed scenes. SyncFix formulates refinement as a joint latent bridge matching problem, synchronizing distorted and clean representations across multiple views to fix the semantic and geometric inconsistencies. This means SyncFix learns a joint conditional over multiple views to enforce consistency throughout the denoising trajectory. Our training is done only on image pairs, but it generalizes naturally to an arbitrary number of views during inference. Moreover, reconstruction quality improves with additional views, with diminishing returns at higher view counts. Qualitative and quantitative results demonstrate that SyncFix consistently generates high-quality reconstructions and surpasses current state-of-the-art baselines, even in the absence of clean reference images. SyncFix achieves even higher fidelity when sparse references are available."
#                        )
#         processor = HostedLLMProcessor(keywords=keywords,api_key=settings.llm_api_key,provider_url=settings.llm_host)
#         score = await processor.evaluate_abstract(art1)

#         assert score is not None
#         assert score.score >= 0 and score.score <= 1
#         assert score.score < 0.9
#         assert score.score > 0.6