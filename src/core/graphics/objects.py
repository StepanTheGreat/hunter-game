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

class ReservedMeshCPU:
    "A mesh with preallocated geometry arrays. Highly useful for highly dynamic data"
    def __init__(self, vertex_size: int, index_size: int):
        self.vertex_size = vertex_size
        self.index_size = index_size

        self.verticies = np.zeros(vertex_size, dtype=np.float32)
        self.indices = np.zeros(index_size, dtype=np.uint32)

        # Pointers to free index locations
        self.vertex_ptr = 0
        self.index_ptr = 0

        self.free_index = 0

    def can_fit(self, verticies: int, indices: int) -> bool:
        "Check whether this amount of verticies and indices can be fit into a mesh"
        return (
            verticies <= len(self.verticies)-self.vertex_ptr 
            and
            indices <= len(self.indices)-self.index_ptr 
        )

    def push_geometry(self, verticies: np.ndarray, indices: np.ndarray):
        # Datatypes should be equal
        assert verticies.dtype == self.verticies.dtype and indices.dtype == self.indices.dtype

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
        
        # Insert our 2 new arrays at free locations
        self.verticies[self.vertex_ptr:self.vertex_ptr+len(verticies)] = verticies
        self.indices[self.index_ptr:self.index_ptr+len(indices)] = indices

        # Increment our array pointers
        self.vertex_ptr += len(verticies)
        self.index_ptr += len(indices)

    def can_fit_geometry(self, verticies: np.ndarray, indices: np.ndarray) -> bool:
        return self.can_fit(len(verticies), len(indices))
    
    def can_fit_mesh(self, mesh: "DumbMeshCPU") -> bool:
        return self.can_fit_geometry(mesh.verticies, mesh.indices)

    def push_mesh(self, mesh: "DumbMeshCPU"):
        """
        Push a dumb mesh onto this static mesh. 
        
        First make sure to check if it can even fit with `can_fit_mesh`
        """
        self.push_geometry(mesh.verticies, mesh.indices.copy())

    def get_verticies(self) -> np.ndarray:
        "Get a slice of verticies with actual data. Not all parts of the array are filled with actual data"
        return self.verticies[:self.vertex_ptr]
    
    def get_indices(self) -> np.ndarray:
        "Get a slice of indices with actual data. Not all parts of the array are filled with actual data"
        return self.indices[:self.index_ptr]

    def vertex_elements(self) -> int:
        return self.vertex_ptr
    
    def index_elements(self) -> int:
        return self.index_ptr
    
    def is_empty(self) -> bool:
        return self.vertex_ptr == 0 or self.index_ptr == 0
    
    def clear(self):
        "Reset the internal vertex and index pointer. This essentially \"clears\" space in the array"
        self.vertex_ptr = 0
        self.index_ptr = 0
        self.free_index = 0

class DumbMeshCPU:
    """
    A growable, primitve mesh implementation. It's dumb because it doesn't have a static size, thus all merge
    operation will lead in new array allocations.

    Okay for static data, but not for dynamic.
    """
    def __init__(self, verticies: np.ndarray, indices: np.ndarray):
        
        assert verticies.dtype == np.float32 and indices.dtype == np.uint32

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

        assert verticies.dtype == self.verticies.dtype and indices.dtype == self.indices.dtype

        assert verticies.size > 0 and indices.size > 0
        
        new_index_offset = indices.max()+1
        indices += self.free_index
        self.free_index += new_index_offset
        
        self.verticies = np.append(self.verticies, verticies)
        self.indices = np.append(self.indices, indices)

    def add_mesh(self, other: "DumbMeshCPU"):
        "The same as `add_geometry`, but works on meshes. The mesh will not get modified"
        self.add_geometry(other.verticies, other.indices.copy())

    def vertex_elements(self) -> int:
        return len(self.verticies)

    def index_elements(self) -> int:
        return len(self.indices)

    def is_empty(self) -> bool:
        "Is this mesh empty? (i.e. doesn't contain any geometry)"
        return self.verticies.size == 0 or self.indices.size == 0

class Model:
    "A model is a combination of a CPU mesh and a material. It has all the neccessary information to be rendered"
    def __init__(self, ctx: gl.Context, mesh: DumbMeshCPU, pipeline: Pipeline):
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
