import numpy as np
import moderngl as gl

from modules.numpylist import NumpyList

class PipelineParams:
    "Pipeline parameters control settings like face culling, depth testing, drawing mode and so on"
    def __init__(
            self,
            cull_face: bool,
            depth_test: bool,
            alpha_blending: bool,
            mode: int = gl.TRIANGLES
        ):
        self.cull_face: bool = cull_face
        self.depth_test: bool = depth_test
        self.alpha_blending: bool = alpha_blending
        self.mode: int = mode

    def __eq__(self, other: "PipelineParams") -> bool:
        return all((
            self.cull_face == other.cull_face,
            self.depth_test == other.depth_test,
            self.alpha_blending == other.alpha_blending,
            self.mode == other.mode
        ))
    
    def apply(self, ctx: gl.Context):
        for setting, to in (
            (gl.ONE_MINUS_SRC_ALPHA, self.alpha_blending),
            (gl.DEPTH_TEST, self.depth_test), 
            (gl.CULL_FACE, self.cull_face),
        ):
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

    def __eq__(self, other: "Pipeline"):
        return (
            self.params == other.params and 
            self.program == other.program and
            self.vertex_attributes == other.vertex_attributes
        )
    
    def __setitem__(self, key: str, value):
        self.program[key] = value

    def apply_params(self):
        "Prepare all the local material's variables for the draw operation"
        self.params.apply(self.ctx)

    def get_mode(self) -> int:
        "Get draw mode"
        return self.params.mode

class ReservedMeshCPU:
    "A mesh with preallocated geometry arrays. Highly useful for highly dynamic data"
    def __init__(self, vertex_size: int, index_size: int, vertex_dtype: np.dtype = np.float32):
        self.vertex_size = vertex_size
        self.index_size = index_size

        self.verticies = NumpyList(reserve=vertex_size, dtype=vertex_dtype)
        self.indices = NumpyList(reserve=index_size, dtype=np.uint32)

        self.free_index = 0

    def get_vertex_dtype(self) -> np.dtype:
        return self.verticies.dtype()

    def can_fit(self, verticies: int, indices: int) -> bool:
        "Check whether this amount of verticies and indices can be fit into a mesh"
        return (
            verticies <= self.vertex_size-len(self.verticies) 
            and
            indices <= self.index_size-len(self.indices) 
        )

    def push_geometry(self, verticies: np.ndarray, indices: np.ndarray):
        # Obviously there's no reason to push empty arrays
        assert verticies.size > 0 and indices.size > 0

        # We can't do anything if the geometry can't even fit into our arrays
        assert self.can_fit(len(verticies), len(indices))
        
        # Get the maximum index in the index array
        new_index_offset = indices.max()

        # Increment all indices in the index array by our free_index
        indices += self.free_index

        # Increment our free index by the max index array's index + 1
        self.free_index += new_index_offset+1
        
        # Append our 2 new arrays
        self.verticies.append(verticies)
        self.indices.append(indices)

    def can_fit_geometry(self, verticies: np.ndarray, indices: np.ndarray) -> bool:
        return self.can_fit(len(verticies), len(indices))
    
    def can_fit_mesh(self, mesh: "DynamicMeshCPU") -> bool:
        return self.can_fit(mesh.vertex_elements(), mesh.index_elements())

    def push_mesh(self, mesh: "DynamicMeshCPU"):
        """
        Push a dumb mesh onto this static mesh. 
        
        First make sure to check if it can even fit with `can_fit_mesh`
        """
        self.push_geometry(mesh.get_verticies(), mesh.get_indices().copy())

    def get_verticies(self) -> np.ndarray:
        "Get a slice of verticies with actual data. Not all parts of the array are filled with actual data"
        return self.verticies.get_array()
    
    def get_indices(self) -> np.ndarray:
        "Get a slice of indices with actual data. Not all parts of the array are filled with actual data"
        return self.indices.get_array()

    def vertex_elements(self) -> int:
        return len(self.verticies)
    
    def index_elements(self) -> int:
        return len(self.indices)
    
    def is_empty(self) -> bool:
        return self.verticies.is_empty() or self.indices.is_empty()
    
    def clear(self):
        "Reset the internal vertex and index pointer. This essentially \"clears\" space in the array"
        self.verticies.clear()
        self.indices.clear()
        self.free_index = 0

class DynamicMeshCPU:
    """
    A growable CPU mesh. It's no longer dumb!

    Okay for static data, but not for dynamic.
    """
    def __init__(self, verticies: np.ndarray, indices: np.ndarray, vertex_dtype: np.dtype = np.float32):
        
        assert verticies.dtype == vertex_dtype and indices.dtype == np.uint32

        self.verticies = NumpyList(verticies, dtype=vertex_dtype)
        self.indices = NumpyList(indices, dtype=np.uint32)

        self.free_index = indices.max()+1 if indices.size > 0 else 0

    def get_vertex_dtype(self) -> np.dtype:
        return self.verticies.dtype()

    def add_geometry(self, verticies: np.ndarray, indices: np.ndarray):
        """
        Add vertex and index arrays to this mesh.
        The indices in the index array will automatically get incremented.
        
        ## Warning
        The index array will be modified during the call, so make sure to clone it if you're going to use it later.
        """
        assert verticies.size > 0 and indices.size > 0
        
        new_index_offset = indices.max()+1
        indices += self.free_index
        self.free_index += new_index_offset
        
        self.verticies.append(verticies)
        self.indices.append(indices)

    def add_mesh(self, other: "DynamicMeshCPU"):
        "The same as `add_geometry`, but works on meshes. The mesh will not get modified"
        self.add_geometry(other.get_verticies(), other.get_indices().copy())

    def get_verticies(self) -> np.ndarray:
        return self.verticies.get_array()
    
    def get_indices(self) -> np.ndarray:
        return self.indices.get_array()

    def vertex_elements(self) -> int:
        return len(self.verticies)

    def index_elements(self) -> int:
        return len(self.indices)
    
    def vertex_capacity(self) -> int:
        return self.verticies.capacity()
    
    def index_capacity(self) -> int:
        return self.indices.capacity()

    def is_empty(self) -> bool:
        "Is this mesh empty? (i.e. doesn't contain any geometry)"
        return self.verticies.is_empty() or self.indices.is_empty()

class Model:
    "A model is a combination of a CPU mesh and a material. It has all the neccessary information to be rendered"
    def __init__(
        self, 
        ctx: gl.Context, 
        mesh: DynamicMeshCPU, 
        pipeline: Pipeline, 
        dynamic_buffers: bool = False,
        vertex_format: str = None
    ):
        self.ctx = ctx
        
        self.mesh = mesh
        self.pipeline = pipeline
        self.vertex_format = vertex_format

        self.is_dynamic = dynamic_buffers

        self.vbo = self.ctx.buffer(
            reserve=mesh.vertex_capacity()*self.mesh.get_vertex_dtype().itemsize, 
            dynamic=self.is_dynamic
        )
        self.ibo = self.ctx.buffer(reserve=mesh.index_capacity()*4, dynamic=self.is_dynamic)
        self.vertices_to_draw = mesh.index_elements()

        self.vao: gl.VertexArray = None
        self._make_vao(pipeline)

        self.sync_mesh()

    def _make_vao(self, pipeline: Pipeline):
        if self.vao:
            self.vao.release()

        if self.vertex_format is None:
            self.vao = self.ctx.vertex_array(
                pipeline.program, 
                self.vbo,
                *self.pipeline.vertex_attributes,
                index_buffer=self.ibo
            )
        else:
            self.vao = self.ctx.vertex_array(
                pipeline.program, 
                [
                    (self.vbo, self.vertex_format, *self.pipeline.vertex_attributes)
                ],
                index_buffer=self.ibo
            )

    def render(self, vertices: int = -1, first: int = 0, instances: int = -1):
        self.pipeline.apply_params()
        vertices = self.vertices_to_draw if vertices == -1 else vertices
        self.vao.render(self.pipeline.get_mode(), vertices, first, instances)  

    def get_mesh(self) -> DynamicMeshCPU:
        return self.mesh
    
    def sync_mesh(self):
        """
        When updating a model's mesh, it also needs to be syncronized on the GPU. For this exact reason
        you should use this method (but, only when changes are really neccessary).

        A model takes into account the capacity of the mesh (the capacity of its index and vertex array).
        If your mesh changes its capacity - the model will recreate its GPU buffers, recopying the internal data;
        In any other case it will just rewrite the buffers, which is pretty efficient (even more if the model is dynamic)

        Overall, don't use this method too often, since it's expensive.
        """

        rebuild_vao = False

        vertex_size = int(self.mesh.get_vertex_dtype().itemsize)

        # Update the vertex buffer
        if self.mesh.vertex_elements()*vertex_size > self.vbo.size:
            rebuild_vao = True
            self.vbo.release()
            self.vbo = self.ctx.buffer(reserve=self.mesh.vertex_capacity()*vertex_size, dynamic=self.is_dynamic)

        self.vbo.write(self.mesh.get_verticies())

        # Update the index buffer
        if self.mesh.index_elements()*4 > self.ibo.size:
            rebuild_vao = True
            self.ibo.release()
            self.ibo = self.ctx.buffer(reserve=self.mesh.index_capacity()*4, dynamic=self.is_dynamic)
        
        self.ibo.write(self.mesh.get_indices())
        
        # If neccessary, rebuild the vertex attribute array
        if rebuild_vao:
            self._make_vao()
        
        self.vertices_to_draw = self.mesh.index_elements()

    def release(self):
        """
        Release this model by cleaning its vertex, index buffers and vertex array object. Doesn't
        release the pipeline however. 
        """

        self.vbo.release()
        self.ibo.release()
        self.vao.release()
