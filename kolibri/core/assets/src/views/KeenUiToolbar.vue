<script>

  import UiToolbar from 'kolibri-design-system/lib/keen/UiToolbar';

  export default {
    name: 'KeenUiToolbar',
    extends: UiToolbar,
  };

</script>


<style lang="scss" scoped>

  /deep/ .ui-toolbar__title {
    overflow: hidden;
    white-space: nowrap;
  }

  /deep/ .ui-toolbar__left {
    display: flex;
    align-items: center;
    margin-left: 16px;
  }

  /deep/ .ui-toolbar__brand {
    min-width: inherit;
  }

  .ui-toolbar {
    padding: 0 16px;
  }

</style>
