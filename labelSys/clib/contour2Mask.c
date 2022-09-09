
#define COORD_MAX 999999
#define COORD_MIN 0
#define FALSE 0
#define TRUE 1

/* #include <stdio.h> */

typedef unsigned char bool;

typedef unsigned char arr_t;
typedef int coord_t;

// HEADER
bool checkLineRelation( 
        coord_t x, coord_t y, 
        coord_t x0, coord_t y0, 
        coord_t x1, coord_t y1,
        int * counter
        );

// global 
coord_t IM_W;
coord_t IM_H;
// 以免重复计算顶点
coord_t PREV_VERT0[2];

// cnt_len: 2 * n_points
bool isInside(coord_t x, coord_t y, coord_t * cnt, unsigned int cnt_len){
    // further check using intersection
    // check the number of intersections drawing horizontal line towards right (x axis + direction)
    int intersection_counter[1];
    * intersection_counter = 0;

    // line ends
    coord_t x0, x1, y0, y1;

    // traverse the contour
    //
    // set previous line to the last-fist vertices
    PREV_VERT0[0] = cnt[cnt_len-2];
    PREV_VERT0[1] = cnt[cnt_len-1];

    /* printf("-----point(%d, %d) (cnt_len: %d)---------\n", x, y, cnt_len); */
    for (unsigned int i=0; i<cnt_len-3; i = i+2){
        x0 = cnt[i];
        y0 = cnt[i+1];
        x1 = cnt[i+2];
        y1 = cnt[i+3];

        if (checkLineRelation(x, y, x0, y0, x1, y1, intersection_counter)){
            return TRUE;
        }

        PREV_VERT0[0] = x0;
        PREV_VERT0[1] = y0;
    }

    // Take into account the last and the first point-line
    if (checkLineRelation(x, y,
                cnt[cnt_len-2], cnt[cnt_len-1],
                cnt[0], cnt[1], intersection_counter)){
        return TRUE;
    }
    

    if (* intersection_counter % 2 == 0){
        return FALSE;
    }
    return TRUE;
}

/*
 * return TRUE if point is on the line
 * else return FALSE and maybe modify intersection_count
 * */
bool checkLineRelation( 
        coord_t x, coord_t y, 
        coord_t x0, coord_t y0, 
        coord_t x1, coord_t y1,
        int * counter
        ){

        /* printf("line: %ld, %ld - %ld, %ld\n", x0, y0, x1, y1); */

        // whole line on the left side
        if (x0 < x && x1 < x){
            return FALSE;
        }

        // whole line on above or below
        if ((y0 < y && y1 < y) || (y0 > y && y1 > y)){
            return FALSE;
        }

        // point just on line ends
        if ((x0 == x && y0 == y) || (x1 == x && y1 == y)){
            return TRUE;
        }

        // horizontal line at y level
        if (y0 == y1) {
            if (!(x0 > x && x1 > x)){
                // x in line-x range
                return TRUE;
            }
            else {
                // x out of the line-x range
                return FALSE;
            }
        }

        if (x1 == x0){
            // count before ?
            if (!(y==y0 || y==y1)){
                // y==y0ory1 will be considered below
                * counter = *counter +1;
            }
            return FALSE;
        }

        // one end at the point's y level (at leaset on end on right side)
        // previous vertice's y
        coord_t y0_p = PREV_VERT0[1];
        if (y==y0){
            if(x<x0){
                if ((y - y0_p)*(y - y1) <= 0){
                    // only count when two lines on the x-axis' different sides
                    *counter = *counter + 1;
                    /* printf("\tCount y=y0 (counter: %d)\n", *counter); */
                }
            }
            return FALSE;
        }
        else if (y==y1){
            // Will be counted when y==y0 on next line
            return FALSE;
        }

        // Calculate intersection
        long xi = (long) (
                (double)x0 + ((double)y - (double)y0)/((double)y1 - (double)y0) * ((double)x1 - (double)x0)
                );
        if (xi == x){
            // point on the line
            return TRUE;
        }
        if (xi > x){
            * counter = * counter + 1;
            /* printf("\tFind intersection: x - %ld (counter: %d)\n", xi, *counter); */
        }
        return FALSE;

}

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
    
    // Init global variables
    IM_H = H;
    IM_W = W;

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

        // traverse all pixels
        for (coord_t y = 0; y < H; y++){
            for (coord_t x = 0; x < W; x++){
                // if point is outside of the bounding box, the point is not inside contour, continue
                if (x < bbox_x_min || x > bbox_x_max || y < bbox_y_min || y > bbox_y_max){
                    continue;
                }

                // reset PREV_LINE
                PREV_VERT0[0] = COORD_MAX;
                PREV_VERT0[1] = COORD_MAX;
                if (isInside(x, y, cnt, cnt_len)){
                    msk[y*W + x] = dest_val;
                }
            }
        }

        // to the next contour
        cnt += cnt_len;
    }

};


