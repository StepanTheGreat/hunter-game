use std::{
    collections::HashSet, 
    ops::{AddAssign, MulAssign, SubAssign}
};
use pyo3::prelude::*;
use pyo3::types::PyModuleMethods;

const ALMOST_ZERO: f64 = 0.0001;

/// A utility struct purely for convenience reasons.
struct Vec2<T>
where T: PartialEq + AddAssign + SubAssign + MulAssign + Copy {
    pub x: T,
    pub y: T
}

impl<T> Vec2<T>
where T: PartialEq + AddAssign + SubAssign + MulAssign + Copy {
    fn new(x: T, y: T) -> Self {
        Self {
            x,
            y
        }
    }
}

#[pyclass]
pub struct TileMap {
    width: usize,
    height: usize,
    tiles: Vec<Vec<i32>>,
    transparent_tiles: HashSet<i32>
}

#[pymethods]
impl TileMap {
    #[new]
    fn new(width: usize, height: usize, tiles: Option<Vec<Vec<i32>>>) -> Self {
        if let Some(tiles) = &tiles {
            // TODO: In the future there should be an error instead
            if tiles.len() != height {
                panic!("The tilemap height mismatches the gived height");
            }
            if tiles.iter().filter(|row| row.len() == width).count() != height {
                panic!("The tilemap width has incorrect size");
            }
        }

        Self { 
            width,
            height,
            tiles: tiles.unwrap_or(vec![vec![0; width]; height]),
            transparent_tiles: HashSet::new()
        }
    }

    /// Add a tile ID to the transparent tiles hash-set
    pub fn add_transparent_tile(&mut self, tile: i32) {
        self.transparent_tiles.insert(tile);
    }

    pub fn set_tiles(&mut self, tiles: Vec<Vec<i32>>) {
        if tiles.len() != self.height {
            panic!("The tilemap height mismatches the gived height");
        }
        if tiles.iter().filter(|row| row.len() == self.width).count() != self.height {
            panic!("The tilemap width has incorrect size");
        }

        self.tiles = tiles;
    }
}

#[pyclass]
pub struct Caster {
    x: f64,
    y: f64,
    angle: f64,
    rays: i32,
    fov: f64,
    ray_gap: f64,
    max_ray_distance: f64
}

#[pymethods]
impl Caster {
    #[new]
    pub fn new(pos: (f64, f64), angle: f64, rays: i32, fov: f64, max_ray_distance: f64) -> Self {
        let ray_gap = (fov/(rays as f64)).to_radians();
        Self {
            x: pos.0,
            y: pos.1,
            angle,
            rays,
            fov,
            ray_gap,
            max_ray_distance
        }
    }

    pub fn set_pos(&mut self, x: f64, y: f64) {
        self.x = x;
        self.y = y;
    }

    pub fn set_angle(&mut self, angle: f64) {
        self.angle = angle;
    }
}

type RayResult = (i32, f64, f64, f64, bool);

#[pyfunction]
pub fn cast_rays(tilemap: &TileMap, caster: &Caster) -> Vec<Vec<RayResult>> {
    let tiles = &tilemap.tiles;

    let transparent_tiles = &tilemap.transparent_tiles;

    let caster_pos = Vec2::new(caster.x, caster.y);
    let mut results: Vec<Vec<RayResult>> = vec![Vec::with_capacity(4); caster.rays as usize];

    // results = [[] for _ in range(rays)]
    let mut ray_angle = caster.angle-(caster.fov/2.0).to_radians() - caster.ray_gap;
    for ray in 0..caster.rays {
        ray_angle += caster.ray_gap;

        let mut ray_direction: Vec2<f64> = Vec2::new(ray_angle.cos(), ray_angle.sin());
        if ray_direction.x == 0.0 {
            ray_direction.x = ALMOST_ZERO
        }
        if ray_direction.y == 0.0 {
            ray_direction.y = ALMOST_ZERO
        }
        
        // Here we calculate the hypothenuse for each axis.
        // Basically, to move by unit 1 (our grid cell size), how many "steps" do we need with our
        // axis direction?
        // The infinity here is used purely to avoid division by zero

        let ray_step = Vec2::new(
            (1.0 + (ray_direction.y / ray_direction.x).powi(2)).sqrt(),
            (1.0 + (ray_direction.x / ray_direction.y).powi(2)).sqrt()
        );
        // Also god damn it, this line took me multiple hours. I have no idea what magical differences
        // rust and python has in this calculations, but this should be reversed. Damn.

        // A grid integer coordinate. We start with the player position
        // PS: int() for negative values produces a rounding for an opposed direction, which in turn
        // breaks this algorithm (i.e. 0.75 -> 0, while -0.75 -> 0).
        // math.floor will consistenly map the floating point to its lowest, even for negative values
        let (mut grid_x, mut grid_y) = (caster_pos.x.floor() as i32, caster_pos.y.floor() as i32);

        // A fixed integer grid vector direction, for traversing the grid
        let grid_direction: Vec2<i32> = Vec2::new(
            if ray_direction.x > 0.0 { 1 } else { -1 },
            if ray_direction.y > 0.0 { 1 } else { -1 }
        );

        // Not a vector, but instead a 2 value map that allows us to compare 2 axis.
        // In DDA, we move and check the smallest axis, then increase its value.
        // 
        // Here we need to initialize it to the inner-cell position of the player (between 0 and 1),
        // to ensure that the ray doesn't start from the grid position, but from the player's.
        let mut traversed_axis: Vec2<f64> = Vec2::new(
            if ray_direction.x >= 0.0 { 
                (((grid_x+1) as f64)-caster_pos.x) * ray_step.x  
            } else { 
                (caster_pos.x-(grid_x as f64)) * ray_step.x 
            },

            if ray_direction.y >= 0.0 { 
                (((grid_y+1) as f64)-caster_pos.y) * ray_step.y 
            } else { 
                (caster_pos.y-(grid_y as f64)) * ray_step.y
            }
        );

        let mut ray_distance = 0.0;
        let mut y_side;
        let mut ignore_tile: Option<i32> = None;
        while ray_distance < caster.max_ray_distance {
            ray_distance = traversed_axis.x.min(traversed_axis.y);

            if traversed_axis.x <= traversed_axis.y {
                y_side = false;
                traversed_axis.x += ray_step.x;
                grid_x += grid_direction.x;
            } else {
                y_side = true;
                traversed_axis.y += ray_step.y;
                grid_y += grid_direction.y;
            }
            
            if !(
                (grid_x >= 0 && grid_x < (tilemap.width as i32)) &&
                (grid_y >= 0 && grid_y < (tilemap.height as i32))
            ) {
                // If the grid position is out of the tilemap bounds - continue
                continue
            }
            
            if (grid_x >= 0 && grid_x < (tilemap.width as i32)) && (grid_y >= 0 && grid_y < (tilemap.height as i32)){

            }
            let tile = tiles[grid_y as usize][grid_x as usize];
            if tile != 0 {
                match ignore_tile {
                    Some(ignored) if ignored == tile => continue,
                    _ => ()
                };
                if matches!(ignore_tile, Some(ignored_tile) if ignored_tile == tile) {
                    continue;
                }
                
                if ray_distance == 0.0 {
                    ray_distance = ALMOST_ZERO
                }

                // let ray_hit = Vec2::new(
                //     caster_pos.x-ray_direction.x*ray_distance,
                //     caster_pos.y-ray_direction.y*ray_distance
                // );

                ray_distance *= (ray_angle-caster.angle).cos();

                results[ray as usize].push((tile, ray_distance, ray_direction.x, ray_direction.y, y_side));
                
                if transparent_tiles.contains(&tile) {
                    ignore_tile = Some(tile);
                } else {
                    break;
                }
            } else {
                ignore_tile = None;
            }
        }
    }

    results
}

#[pymodule(name = "native")]
fn native_module(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(cast_rays, m)?)?;
    m.add_class::<Caster>()?;
    m.add_class::<TileMap>()?;
    Ok(())
}