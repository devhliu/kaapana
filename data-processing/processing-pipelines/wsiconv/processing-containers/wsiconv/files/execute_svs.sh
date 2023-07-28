echo "Hello World"

find $WORKFLOW_DIR/$OPERATOR_IN_DIR -follow -name '*.svs' -exec ./idc-wsi-conversion/gdcsvstodcm_svs.sh '{}' ';'
