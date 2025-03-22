import numpy as np
import moderngl as gl

class MaterialParams:
    "Material parameters that control settings like face culling, depth testing, drawing mode and so on"
    def __init__(
            self,
            cull_face: bool,
            depth_test: bool,
            mode: int = gl.TRIANGLES
        ):
        self.cull_face: bool = cull_face
        self.depth_test: bool = depth_test
        self.mode: int = mode

    def __eq__(self, other: "MaterialParams") -> bool:
        return (
            self.cull_face == other.cull_face,
            self.depth_test == other.depth_test,
            self.mode == other.mode
        )
    
    def apply(self, ctx: gl.Context):
        for setting, to in ((gl.DEPTH_TEST, self.depth_test), (gl.CULL_FACE, self.cull_face)):
            ctx.enable(setting) if to else ctx.disable(setting)

class Material:
    """
    A material is essentially a shader program and a texture. 
    Materials can also contain their own material-scope uniform variables
    """
    def __init__(self, ctx: gl.Context, program: gl.Program, texture: gl.Texture, params: MaterialParams):
        self.ctx = ctx

        self.params = params
        self.program = program
        self.texture = texture
        self.uniforms = {}

    def __eq__(self, other: "Material"):
        # Materials are only equal when both their programs and textures are
        return self.program == other.program and self.texture == other.texture
    
    def __setitem__(self, key: str, value):
        self.uniforms[key] = value

    def set_texture(self, texture: gl.Texture):
        "Replace material's texture to a new one"
        self.texture = texture

    def prepare(self):
        "Prepare all the local material's variables for the draw operation"
        self.params.apply(self.ctx)
        self.texture.use()
        for key, value in self.uniforms:
            self.program[key] = value

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
    def __init__(self, ctx: gl.Context, mesh: MeshCPU, material: Material, vertex_attributes: tuple):
        self.ctx = ctx
        
        self.mesh = mesh
        self.material = material
        self.vertex_attributes = vertex_attributes

        self.vbo = self.ctx.buffer(mesh.verticies)
        self.ibo = self.ctx.buffer(mesh.indices)
        self.vao = self.ctx.vertex_array(material.program, self.vbo, *vertex_attributes, index_buffer=self.ibo)

    def render(self):
        self.material.prepare()
        self.vao.render()

    def release(self):
        "Release this model by cleaning its vertex, index buffers and vertex array object. Doesn't "
        self.vbo.release()
        self.ibo.release()
        self.vao.release()
