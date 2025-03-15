"""
Geometry batching module that allows grouping geometry based on their material (shaders + uniforms) and textures.
"""

import numpy as np
import moderngl as gl

class Pipeline:
    def __init__(self, ctx: gl.Context, shader_vert: str, shader_frag: str, attributes: list[str]):
        self.program = ctx.program(vertex_shader=shader_vert, fragment_shader=shader_frag)
        self.attributes = attributes
        self.__ctx = ctx

    def get_program(self) -> gl.Program:
        return self.program
    
    def __setitem__(self, name: str, value: any):
        self.program[name] = value

    def make_vbo(self, vbo: gl.Buffer, ibo: gl.Buffer = None) -> gl.VertexArray:
        "Create a vertex attribute object from this pipeline and provided buffers"
        return self.__ctx.vertex_array(self.program, vbo, *self.attributes, index_buffer=ibo)

class BatchGroup:
    """
    A batch-group is a collection of geometry and index buffer based on their texture and (in the future) material.
    """
    def __init__(
            self, 
            texture: gl.Texture, 
            verticies: np.ndarray, 
            indices: np.ndarray,
            pipeline: Pipeline
        ):
        # v means vertex, i means index
        self.vbuffer: gl.Buffer = None
        self.ibuffer: gl.Buffer = None
        self.vao: gl.VertexArray = None

        self.pipeline: Pipeline = pipeline
        self.texture: gl.Texture = texture

        self.__ctx = self.texture.ctx

        # When grouping geometry, it's important to use unique indices for different meshes
        # free index means the index that is free to use. The index however will be incremented automatically
        # internally.
        self.free_index: int = 0
        self.verticies: np.ndarray = np.array([], dtype=np.float32)
        self.indices: np.ndarray = np.array([], dtype=np.uint32)
        self.is_syncronized: bool = False

        # Initialize the starting geometry
        self.push_geometry(verticies, indices)

    def push_geometry(self, verticies: np.ndarray, indices: np.ndarray):
        "Push verticies and indices to the internal buffer, while also incrementing the internal "
        assert verticies.dtype == self.verticies.dtype, "vertex array datatype mismatch"
        assert indices.dtype == self.indices.dtype, "index array datatype mismatch"

        assert len(verticies) > 0, "Can't push an empty geometry array"
        assert len(indices) > 0, "Can't push an empty index array"
        
        new_index_offset = indices.max()+1
        indices += self.free_index
        self.free_index += new_index_offset

        self.verticies = np.append(self.verticies, verticies)
        self.indices = np.append(self.indices, indices)

        self.is_syncronized = False

    def is_sync(self) -> bool:
        """
        Check if this group is syncronized. A group is syncronized when:
            1. It's GPU buffers aren't `None` (i.e. weren't initialized)
            2. The contents of its CPU buffers are syncronized with the contents of its GPU buffers
        """
        return self.is_syncronized

    def sync_buffers(self):
        """
        Syncronize 2 buffers on the GPU. This will do nothing if the group is already syncronized.
        
        If this is a first call, it will create a buffer on the GPU, but in any other case it will delete
        an existing buffer and allocate a new one.

        **DON'T use this for dynamic data, prefer to use this for purely static data that doesn't change frequently
        (like a scene)**
        """

        if self.is_sync():
            return
            
        if not (self.vbuffer is None):
            self.vbuffer.release()
        self.vbuffer = self.__ctx.buffer(self.verticies)

        if not (self.ibuffer is None):
            self.ibuffer.release()
        self.ibuffer = self.__ctx.buffer(self.indices)

        if not (self.vao is None):
            self.vao.release()
        self.vao = self.pipeline.make_vbo(self.vbuffer, self.ibuffer)

        self.is_syncronized = True

    def release(self):
        """Release all GPU buffers and prepare for deletion. This has to be called before deleting the object to prevent memory leaks on the GPU"""

        for obj in (self.ibuffer, self.vbuffer, self.vao):
            if not obj is None:
                obj.release()

    def render(self, mode: int | None = None, vertices: int = -1, first: int = 0):
        assert self.is_sync(), "The group isn't syncronized"
        self.vao.render(mode=mode, vertices=vertices, first=first)

class StaticBatcher:
    def __init__(self):
        self.groups: dict[gl.Texture, BatchGroup] = {}
        self.is_syncronized: bool = True

    def get_group(self, texture: gl.Texture) -> BatchGroup | None:
        """Get a batch group by texture"""
        return self.groups.get(texture)

    def push_geometry(
            self, 
            texture: gl.Texture, 
            verticies: np.ndarray, 
            indices: np.ndarray,
            pipeline: Pipeline
        ):
        group = self.get_group(texture)

        if group is None:
            # Create a new group with given geometry
            self.groups[texture] = BatchGroup(texture, verticies, indices, pipeline)
        else:
            group.push_geometry(verticies, indices)
            
        self.is_syncronized = False

    def sync(self):
        for buffer in self.groups.values():
            # This will do nothing if a buffer is already syncronized
            buffer.sync_buffers()

        self.is_syncronized = True

    def get_batches(self) -> list[tuple[gl.Texture, BatchGroup]]:
        assert self.is_syncronized, "The batcher isn't syncronized. Use the `sync` method to syncronize all its groups"
        return self.groups.items()