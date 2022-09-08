#define COORD_MAX 999999
#define COORD_MIN 0
#define FALSE 0
#define TRUE 1

typedef unsigned char bool;

typedef unsigned char arr_t;
typedef unsigned int coord_t;

struct Point {
    coord_t x;
    coord_t y;
};

struct Contour {
    struct Point * pts;
    unsigned int length;
};

/* 
  Contour to mask,
  Pass-in contour and mask as 1D array, together with their sizes

  Many contours are flattened to 1D and concatenated,
  Pass-in with number of contours: n_cnt
  And contour lengths: cnt_lens (size: n_cnt)

  dest_vals is the designated values for each contour (size: n_cnt)

  Assume OpenCV coordinates
 */
void cnts2msk(
        arr_t * msk, coord_t H, coord_t W, 
        coord_t * cnt,
        unsigned int n_cnt, unsigned int * cnt_lens,
        arr_t * dest_vals
        );

/*
  n_points is 2
  point[0] -> x
  point[1] -> y
 * */
bool isInside(coord_t * point, coord_t * cnt, unsigned int cnt_len){

    coord_t x = point[0];
    coord_t y = point[1];

    // initial screening using bounding box
    
    // bounding box
    coord_t bbox_x_max = COORD_MIN;
    coord_t bbox_x_min = COORD_MAX;
    coord_t bbox_y_max = COORD_MIN;
    coord_t bbox_y_min = COORD_MAX;

    coord_t val;
    // find x extreme
    for (unsigned int i = 0; i < cnt_len; i = i+2){
        val = cnt[i];
        if (val > bbox_x_max){
            bbox_x_max = val;
        }
        else if (val < bbox_x_min){
            bbox_x_min = val;
        }
    }
    // find y extreme
    for (unsigned int j = 1; j < cnt_len; j = j+2){
        val = cnt[j];
        if (val > bbox_y_max){
            bbox_y_max = val;
        }
        else if (val < bbox_y_min){
            bbox_y_min = val;
        }
    }

    // if point is outside of the bounding box, return false
    if (x < bbox_x_min || x > bbox_x_max || y < bbox_y_min || y > bbox_y_max){
        return FALSE;
    }

    // further check using intersection
    // To implement later...
    return TRUE;
};

