
#define COORD_MAX 999999
#define COORD_MIN 0
#define FALSE 0
#define TRUE 1

#include <stdio.h>

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

bool isInside(coord_t x, coord_t y, coord_t * cnt, unsigned int cnt_len){
    // further check using intersection
    // To implement later...
    return TRUE;
};

/* 
  Contours to mask,
  Pass-in contours and mask as 1D array, together with their sizes

  Many contours are flattened to 1D and concatenated,
  Pass-in with number of contours: n_cnt
  And contour lengths (point lengths * 2): cnt_lens (size: n_cnt)

  dest_vals is the designated values for each contour (size: n_cnt)

  Assume OpenCV coordinates
 */
void cnts2msk(
        arr_t * msk, coord_t H, coord_t W, 
        coord_t * contour,
        unsigned int n_cnt, unsigned int * cnt_lens,
        arr_t * dest_vals
        ){

    unsigned int cnt_len;
    arr_t dest_val;
    coord_t * cnt = contour;     // pointer pointing to current contour

    coord_t bbox_x_max;
    coord_t bbox_x_min;
    coord_t bbox_y_max;
    coord_t bbox_y_min;
    for (unsigned int cnt_id = 0; cnt_id < n_cnt; cnt_id ++ ){
        cnt_len = cnt_lens[cnt_id];
        dest_val = dest_vals[cnt_id];

        // bounding box coordinate extremes
        bbox_x_max = COORD_MIN;
        bbox_x_min = COORD_MAX;
        bbox_y_max = COORD_MIN;
        bbox_y_min = COORD_MAX;

        coord_t cval;
        /* //test */
        /* for (unsigned int i = 0; i < cnt_len; i++){ */
        /*     cval = cnt[i]; */
        /*     printf("cval: %d ", cval); */
        /* } */
        /* printf("\n\n"); */

        // find x extreme
        for (unsigned int i = 0; i < cnt_len; i = i+2){
            cval = cnt[i];
            /* printf("cval: %d \n", cval); */
            if (cval > bbox_x_max){
                bbox_x_max = cval;
            }
            if (cval < bbox_x_min){
                bbox_x_min = cval;
            }
        }
        // find y extreme
        for (unsigned int j = 1; j < cnt_len; j = j+2){
            cval = cnt[j];
            if (cval > bbox_y_max){
                bbox_y_max = cval;
            }
            if (cval < bbox_y_min){
                bbox_y_min = cval;
            }
        }
        /* printf("x_min: %d\n", bbox_x_min); */
        /* printf("x_max: %d\n", bbox_x_max); */
        /* printf("y_min: %d\n", bbox_y_min); */
        /* printf("y_max: %d\n", bbox_y_max); */


        // traverse all pixels
        for (coord_t y = 0; y < H; y++){
            for (coord_t x = 0; x < W; x++){
                // if point is outside of the bounding box, the point is not inside contour, continue
                if (x < bbox_x_min || x > bbox_x_max || y < bbox_y_min || y > bbox_y_max){
                    continue;
                }

                if (isInside(x, y, cnt, cnt_len)){
                    msk[y*W + x] = dest_val;
                }
            }
        }

        // to the next contour
        cnt += cnt_len;
    }

};


