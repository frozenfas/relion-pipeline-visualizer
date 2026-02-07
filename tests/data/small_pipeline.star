
# version 50001

data_pipeline_general

_rlnPipeLineJobCounter                     12


# version 50001

data_pipeline_processes

loop_
_rlnPipeLineProcessName #1
_rlnPipeLineProcessAlias #2
_rlnPipeLineProcessTypeLabel #3
_rlnPipeLineProcessStatusLabel #4
Import/job001/       None relion.import.other  Succeeded
Extract/job002/       None relion.extract.reextract  Succeeded
JoinStar/job003/       None relion.joinstar.particles  Succeeded
Refine3D/job004/       None relion.refine3d  Succeeded
MaskCreate/job005/       None relion.maskcreate  Succeeded
Class3D/job006/       None relion.class3d     Failed
Select/job007/ Select/j007_best_class/ relion.select.interactive  Succeeded
CtfRefine/job008/       None relion.ctfrefine  Succeeded
PostProcess/job009/       None relion.postprocess  Succeeded
MultiBody/job010/       None relion.multibody  Succeeded
Subtract/job011/       None relion.subtract    Running


# version 50001

data_pipeline_nodes

loop_
_rlnPipeLineNodeName #1
_rlnPipeLineNodeTypeLabel #2
_rlnPipeLineNodeTypeLabelDepth #3
Import/job001/particles.star ParticleGroupMetadata.star.relion            1
Extract/job002/particles.star ParticleGroupMetadata.star.relion            1
JoinStar/job003/join_particles.star ParticleGroupMetadata.star.relion            1
Refine3D/job004/run_data.star ParticleGroupMetadata.star.relion.refine3d            1
Refine3D/job004/run_class001.mrc DensityMap.mrc.relion.refine3d            1
Refine3D/job004/run_half1_class001_unfil.mrc DensityMap.mrc.relion.halfmap.refine3d            1
Refine3D/job004/run_optimiser.star OptimiserData.star.relion.refine3d            1
MaskCreate/job005/mask.mrc Mask3D.mrc.relion            1
Class3D/job006/run_it025_optimiser.star OptimiserData.star.relion.class3d            1
Class3D/job006/run_it025_class001.mrc DensityMap.mrc.relion.class3d            1
Class3D/job006/run_it025_class002.mrc DensityMap.mrc.relion.class3d            1
Class3D/job006/run_it025_class003.mrc DensityMap.mrc.relion.class3d            1
Select/job007/particles.star ParticleGroupMetadata.star.relion            1
CtfRefine/job008/particles_ctf_refine.star ParticleGroupMetadata.star.relion.ctfrefine            1
PostProcess/job009/postprocess.mrc DensityMap.mrc.relion.postprocess            1
PostProcess/job009/postprocess.star ProcessData.star.relion.postprocess            1
MultiBody/job010/run_optimiser.star OptimiserData.star.relion            1
MultiBody/job010/run_half1_body001_unfil.mrc DensityMap.mrc.relion.halfmap.multibody            1
Subtract/job011/particles_subtracted.star ParticleGroupMetadata.star.relion.subtracted            1


# version 50001

data_pipeline_input_edges

loop_
_rlnPipeLineEdgeFromNode #1
_rlnPipeLineEdgeProcess #2
Import/job001/particles.star Extract/job002/
Extract/job002/particles.star JoinStar/job003/
JoinStar/job003/join_particles.star Refine3D/job004/
Refine3D/job004/run_class001.mrc MaskCreate/job005/
Refine3D/job004/run_data.star Class3D/job006/
Refine3D/job004/run_class001.mrc Class3D/job006/
MaskCreate/job005/mask.mrc Class3D/job006/
Class3D/job006/run_it025_optimiser.star Select/job007/
Refine3D/job004/run_data.star CtfRefine/job008/
CtfRefine/job008/particles_ctf_refine.star PostProcess/job009/
Refine3D/job004/run_half1_class001_unfil.mrc PostProcess/job009/
Refine3D/job004/run_optimiser.star MultiBody/job010/
MultiBody/job010/run_optimiser.star Subtract/job011/


# version 50001

data_pipeline_output_edges

loop_
_rlnPipeLineEdgeProcess #1
_rlnPipeLineEdgeToNode #2
Import/job001/ Import/job001/particles.star
Extract/job002/ Extract/job002/particles.star
JoinStar/job003/ JoinStar/job003/join_particles.star
Refine3D/job004/ Refine3D/job004/run_data.star
Refine3D/job004/ Refine3D/job004/run_class001.mrc
Refine3D/job004/ Refine3D/job004/run_half1_class001_unfil.mrc
Refine3D/job004/ Refine3D/job004/run_optimiser.star
MaskCreate/job005/ MaskCreate/job005/mask.mrc
Class3D/job006/ Class3D/job006/run_it025_optimiser.star
Class3D/job006/ Class3D/job006/run_it025_class001.mrc
Class3D/job006/ Class3D/job006/run_it025_class002.mrc
Class3D/job006/ Class3D/job006/run_it025_class003.mrc
Select/job007/ Select/job007/particles.star
CtfRefine/job008/ CtfRefine/job008/particles_ctf_refine.star
PostProcess/job009/ PostProcess/job009/postprocess.mrc
PostProcess/job009/ PostProcess/job009/postprocess.star
MultiBody/job010/ MultiBody/job010/run_optimiser.star
MultiBody/job010/ MultiBody/job010/run_half1_body001_unfil.mrc
Subtract/job011/ Subtract/job011/particles_subtracted.star

