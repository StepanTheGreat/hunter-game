import numpy as np
import moderngl as gl

class Material:
    """
    A material is essentially a shader program and a texture. 
    Materials can also contain their own material-scope uniform variables
    """
    def __init__(self, program: gl.Program, texture: gl.Texture):
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
        self.texture.use()
        for key, value in self.uniforms:
            self.program[key] = value

class MeshCPU:
    "Model geometry stored on the CPU"
    def __init__(self, verticies: np.array, indices: np.array):
        
        assert verticies.dtype == np.float32
        assert indices.dtype == np.uint32

        self.verticies = verticies
        self.indices = indices

        self.free_index = indices.max()

    def add_geometry(self, verticies: np.array, indices: np.array):
        """
        Add vertex and index arrays to this mesh.
        The indices in the index array will automatically get incremented.
        
        ## Warning
        The index array will be modified during the call, so make sure to clone it if you're going to use it later.
        """

        assert verticies.dtype == self.verticies.dtype
        assert indices.dtype == self.indices.dtype

        assert len(verticies) > 0
        assert len(indices) > 0
        
        new_index_offset = indices.max()+1
        indices += self.free_index
        self.free_index += new_index_offset

        self.verticies = np.append(self.verticies, verticies)
        self.indices = np.append(self.indices, indices)

    def add_mesh(self, other: "MeshCPU"):
        "The same as `add_geometry`, but works on meshes. The mesh will not get modified"
        self.add_geometry(other.verticies, other.indices.copy())

class Model:
    "A model is a combination of a CPU mesh and a material. It has all the neccessary information to be rendered"
    def __init__(self, mesh: MeshCPU, material: Material, vertex_attributes: tuple):
        self.__ctx = gl.get_context()
        
        self.mesh = mesh
        self.material = material
        self.vertex_attributes = vertex_attributes

        self.vbo = self.__ctx.buffer(mesh.verticies)
        self.ibo = self.__ctx.buffer(mesh.indices)
        self.vao = self.__ctx.vertex_array(material.program, self.vbo, *vertex_attributes, index_buffer=self.ibo)

    def render(self):
        self.material.prepare()
        self.vao.render()

    def release(self):
        "Release this model by cleaning its vertex, index buffers and vertex array object. Doesn't "
        self.vbo.release()
        self.ibo.release()
        self.vao.release()
