import numpy as np
import moderngl as gl

class PipelineParams:
    "Pipeline parameters control settings like face culling, depth testing, drawing mode and so on"
    def __init__(
            self,
            cull_face: bool,
            depth_test: bool,
            mode: int = gl.TRIANGLES
        ):
        self.cull_face: bool = cull_face
        self.depth_test: bool = depth_test
        self.mode: int = mode

    def __eq__(self, other: "PipelineParams") -> bool:
        return (
            self.cull_face == other.cull_face,
            self.depth_test == other.depth_test,
            self.mode == other.mode
        )
    
    def apply(self, ctx: gl.Context):
        for setting, to in ((gl.DEPTH_TEST, self.depth_test), (gl.CULL_FACE, self.cull_face)):
            ctx.enable(setting) if to else ctx.disable(setting)

class Pipeline:
    """
    A pipeline is essentially a combination of a shader program, draw settings `PipelineParams` and vertex
    attribute descriptions.

    It makes it extremely convenient to construct and reuse
    """
    def __init__(
            self, 
            ctx: gl.Context, 
            program: gl.Program, 
            params: PipelineParams, 
            vertex_attributes=tuple[str, ...]
        ):
        self.ctx = ctx

        self.params = params
        self.program = program
        self.vertex_attributes = vertex_attributes
    
    def __setitem__(self, key: str, value):
        self.program[key] = value

    def apply_params(self):
        "Prepare all the local material's variables for the draw operation"
        self.params.apply(self.ctx)

class MeshCPU:
    "Model geometry stored on the CPU"
    def __init__(self, verticies: np.ndarray, indices: np.ndarray):
        
        assert verticies.dtype == np.float32
        assert indices.dtype == np.uint32

        self.verticies = verticies
        self.indices = indices

        self.free_index = indices.max() if indices.size > 0 else 0

    def add_geometry(self, verticies: np.ndarray, indices: np.ndarray):
        """
        Add vertex and index arrays to this mesh.
        The indices in the index array will automatically get incremented.
        
        ## Warning
        The index array will be modified during the call, so make sure to clone it if you're going to use it later.
        """

        assert verticies.dtype == self.verticies.dtype
        assert indices.dtype == self.indices.dtype

        assert verticies.size > 0
        assert indices.size > 0
        
        new_index_offset = indices.max()+1
        indices += self.free_index
        self.free_index += new_index_offset

        self.verticies = np.append(self.verticies, verticies)
        self.indices = np.append(self.indices, indices)

    def add_mesh(self, other: "MeshCPU"):
        "The same as `add_geometry`, but works on meshes. The mesh will not get modified"
        self.add_geometry(other.verticies, other.indices.copy())

    def is_empty(self) -> bool:
        "Is this mesh empty? (i.e. doesn't contain any geometry)"
        return self.verticies.size == 0 or self.indices.size == 0

class Model:
    "A model is a combination of a CPU mesh and a material. It has all the neccessary information to be rendered"
    def __init__(self, ctx: gl.Context, mesh: MeshCPU, pipeline: Pipeline):
        self.ctx = ctx
        
        self.mesh = mesh
        self.pipeline = pipeline

        self.vbo = self.ctx.buffer(mesh.verticies)
        self.ibo = self.ctx.buffer(mesh.indices)
        self.vao = self.ctx.vertex_array(pipeline.program, self.vbo, *pipeline.vertex_attributes, index_buffer=self.ibo)

    def render(self, vertices: int = -1, first: int = 0, instances: int = -1):
        self.pipeline.apply_params()
        self.vao.render(self.pipeline.params.mode, vertices, first, instances)

    def release(self):
        "Release this model by cleaning its vertex, index buffers and vertex array object. Doesn't "
        self.vbo.release()
        self.ibo.release()
        self.vao.release()
